import json
import os
import urllib
from typing import Any

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pynpm import NPMPackage

from .protocols import get_next_item_dynamic, get_next_item_taskbased
from .utils import ROOT, load_progress_data, save_progress_data

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

tasks_data = {}
progress_data = load_progress_data(warn="No progress.json found. Running, but no campaign will be available.")

# load all tasks into data_all
for campaign_id in progress_data.keys():
    with open(f"{ROOT}/data/tasks/{campaign_id}.json", "r") as f:
        tasks_data[campaign_id] = json.load(f)

# print access dashboard URL for all campaigns
print(
    list(tasks_data.values())[0]["info"]["url"] + "/dashboard.html?" + "&".join([
        f"campaign_id={urllib.parse.quote_plus(campaign_id)}&token={campaign_data["token"]}"
        for campaign_id, campaign_data in tasks_data.items()
    ])
)

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
    save_progress_data(progress_data)

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

    if tasks_data[campaign_id]["info"]["type"] == "task-based":
        return get_next_item_taskbased(campaign_id, user_id, tasks_data, progress_data)
    elif tasks_data[campaign_id]["info"]["type"] == "dynamic":
        return get_next_item_dynamic(campaign_id, user_id, tasks_data, progress_data)
    else:
        return JSONResponse(content={"error": "Unknown campaign type"}, status_code=400)


class DashboardDataRequest(BaseModel):
    campaign_id: str
    token: str | None = None

@app.post("/dashboard-data")
async def dashboard_data(request: DashboardDataRequest):
    campaign_id = request.campaign_id

    is_privileged = (request.token == tasks_data[campaign_id]["token"])

    if campaign_id not in progress_data:
        return JSONResponse(content={"error": "Unknown campaign ID"}, status_code=400)

    progress_new = {
        user_id: {
            **user_val,
            "total": len(tasks_data[campaign_id]["data"][user_id]),
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

    if campaign_id not in progress_data:
        return JSONResponse(content={"error": "Unknown campaign ID"}, status_code=400)
    if token != tasks_data[campaign_id]["token"]:
        return JSONResponse(content={"error": "Invalid token"}, status_code=400)
    if user_id not in progress_data[campaign_id]:
        return JSONResponse(content={"error": "Unknown user ID"}, status_code=400)
    
    # TODO: change this to something smartner in the future
    progress_data[campaign_id][user_id]["progress"] = 0
    progress_data[campaign_id][user_id]["time_start"] = None
    progress_data[campaign_id][user_id]["time_end"] = None
    progress_data[campaign_id][user_id]["time"] = 0
    save_progress_data(progress_data)


@app.get("/download-annotations")
async def download_annotations(
        campaign_id: list[str] = Query(),
        # NOTE: currently not checking tokens for progress download as it is non-destructive
        # token: list[str] = Query()
    ):

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
        token: list[str] = Query()
    ):
    
    if len(campaign_id) != len(token):
        return JSONResponse(content={"error": "Mismatched campaign_id and token count"}, status_code=400)

    output = {}
    for campaign_id, campaign_id in enumerate(campaign_id):
        if campaign_id not in progress_data:
            return JSONResponse(content={"error": f"Unknown campaign ID {campaign_id}"}, status_code=400)
        if token[campaign_id] != tasks_data[campaign_id]["token"]:
            return JSONResponse(content={"error": f"Invalid token for campaign ID {campaign_id}"}, status_code=400)
        
        output[campaign_id] = progress_data[campaign_id]

    return JSONResponse(content=output, status_code=200)

app.mount("/", StaticFiles(directory="src/static", html=True), name="static")