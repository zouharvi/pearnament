import json
import os
from typing import Any

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pynpm import NPMPackage

from .protocols import get_next_item_dynamic, get_next_item_taskbased
from .utils import ROOT

os.makedirs("data/outputs", exist_ok=True)

# build frontend
pkg = NPMPackage('src/web/package.json')
pkg.install()
pkg.run_script('build')

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

data_all = {}


if not os.path.exists("data/progress.json"):
    print("No progress.json found. Running, but no campaign will be available.")
    progress_data = {}
else:
    with open("data/progress.json", "r") as f:
        progress_data = json.load(f)


class LogResponseRequest(BaseModel):
    campaign_id: str
    user_id: str
    payload: Any


@app.post("/log-response")
async def log_response(request: LogResponseRequest):
    global progress_data

    campaign_id = request.campaign_id
    user_id = request.user_id
    payload = json.dumps(request.payload, ensure_ascii=False)

    if campaign_id not in progress_data:
        return JSONResponse(content={"error": "Unknown campaign ID"}, status_code=400)
    if user_id not in progress_data[campaign_id]:
        return JSONResponse(content={"error": "Unknown user ID"}, status_code=400)

    with open(f"{ROOT}/data/outputs/{campaign_id}.jsonl", "a") as log_file:
        log_file.write(payload + "\n")

    # if actions were submitted, we can log time data
    if "actions" in request.payload:
        times = [
            x["time"] for x in request.payload["actions"]
        ]
        if progress_data[campaign_id][user_id]["time_start"] is None:
            progress_data[campaign_id][user_id]["time_start"] = min(times)
        progress_data[campaign_id][user_id]["time_end"] = max(times)
        progress_data[campaign_id][user_id]["time"] += sum([
            min(b - a, 60)
            for a, b in zip(times, times[1:])
        ])

    # TODO: this should verify that the correct ID is being incremented, otherwise prevent incrementing
    progress_data[campaign_id][user_id]["progress"] += 1
    with open(f"{ROOT}/data/progress.json", "w") as f:
        json.dump(progress_data, f, indent=2)

    return JSONResponse(content={"status": "ok"}, status_code=200)


class NextItemRequest(BaseModel):
    campaign_id: str
    user_id: str


@app.post("/get-next-item")
async def get_next_item(request: NextItemRequest):
    campaign_id = request.campaign_id
    user_id = request.user_id

    if campaign_id not in progress_data:
        return JSONResponse(content={"error": "Unknown campaign ID"}, status_code=400)
    if user_id not in progress_data[campaign_id]:
        return JSONResponse(content={"error": "Unknown user ID"}, status_code=400)

    if campaign_id not in data_all:
        # load campaign data if does not exist in cache
        with open(f"{ROOT}/data/tasks/{campaign_id}.json", "r") as f:
            data_all[campaign_id] = json.load(f)

    if data_all[campaign_id]["info"]["type"] == "task-based":
        return get_next_item_taskbased(campaign_id, user_id, data_all, progress_data)
    elif data_all[campaign_id]["info"]["type"] == "dynamic":
        return get_next_item_dynamic(campaign_id, user_id, data_all, progress_data)
    else:
        return JSONResponse(content={"error": "Unknown campaign type"}, status_code=400)


class DashboardDataRequest(BaseModel):
    campaign_id: str


@app.post("/dashboard-data")
async def dashboard_data(request: DashboardDataRequest):
    campaign_id = request.campaign_id

    # TODO: manage dashboard tokens
    is_privileged = True

    if campaign_id not in progress_data:
        return JSONResponse(content={"error": "Unknown campaign ID"}, status_code=400)

    if campaign_id not in data_all:
        # load campaign data if does not exist in cache
        with open(f"{ROOT}/data/tasks/{campaign_id}.json", "r") as f:
            data_all[campaign_id] = json.load(f)

    progress_new = {
        user_id: {
            **user_val,
            "total": len(data_all[campaign_id]["data"][user_id]),
        } | (
            # override if not privileged
            {
                "token_correct": None,
                "token_incorrect": None,
            } if not is_privileged else {}
        )
        for user_id, user_val in progress_data[campaign_id].items()
    }

    return JSONResponse(
        content={
            "status": "ok",
            "data": progress_new
        },
        status_code=200
    )


class ResetTaskRequest(BaseModel):
    campaign_id: str
    user_id: str
    token: str


@app.post("/reset-task")
async def reset_task(request: ResetTaskRequest):
    # ruff: noqa: F841
    campaign_id = request.campaign_id
    user_id = request.user_id
    token = request.token

    return JSONResponse(content={"error": "Resetting tasks is not supported yet"}, status_code=400)


@app.get("/download-annotations")
async def download_annotations(
        campaign_id: list[str] = Query(),
        token: list[str] = Query()):
    if len(campaign_id) != len(token):
        return JSONResponse(content={"error": "Mismatched campaign_id and token count"}, status_code=400)

    # TODO: handle token

    output = {}
    for campaign_id in campaign_id:
        output_path = f"{ROOT}/data/outputs/{campaign_id}.jsonl"
        if campaign_id not in progress_data:
            return JSONResponse(content={"error": f"Unknown campaign ID {campaign_id}"}, status_code=400)
        if not os.path.exists(output_path):
            output[campaign_id] = []
        else:
            with open(output_path, "r") as f:
                output[campaign_id] = [json.loads(x) for x in f.readlines()]

    return JSONResponse(content=output, status_code=200)


@app.get("/download-progress")
async def download_progress(
        campaign_id: list[str] = Query(),
        token: list[str] = Query()):
    if len(campaign_id) != len(token):
        return JSONResponse(content={"error": "Mismatched campaign_id and token count"}, status_code=400)

    # TODO: handle token

    output = {}
    for campaign_id in campaign_id:
        if campaign_id not in progress_data:
            return JSONResponse(content={"error": f"Unknown campaign ID {campaign_id}"}, status_code=400)
        
        output[campaign_id] = progress_data[campaign_id]

    return JSONResponse(content=output, status_code=200)

app.mount("/", StaticFiles(directory="src/static", html=True), name="static")