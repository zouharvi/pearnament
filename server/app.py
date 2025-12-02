import json
import os
from typing import Any

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .assignment import get_next_item, reset_task, update_progress
from .utils import ROOT, load_progress_data, save_progress_data

os.makedirs(f"{ROOT}/data/outputs", exist_ok=True)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

tasks_data = {}
progress_data = load_progress_data(
    warn="No progress.json found. Running, but no campaign will be available.")

# load all tasks into data_all
for campaign_id in progress_data.keys():
    with open(f"{ROOT}/data/tasks/{campaign_id}.json", "r") as f:
        tasks_data[campaign_id] = json.load(f)


class LogResponseRequest(BaseModel):
    campaign_id: str
    user_id: str
    item_i: int
    payload: Any


@app.post("/log-response")
async def _log_response(request: LogResponseRequest):
    global progress_data

    campaign_id = request.campaign_id
    user_id = request.user_id

    if campaign_id not in progress_data:
        return JSONResponse(content={"error": "Unknown campaign ID"}, status_code=400)
    if user_id not in progress_data[campaign_id]:
        return JSONResponse(content={"error": "Unknown user ID"}, status_code=400)

    # append response to the output log
    with open(f"{ROOT}/data/outputs/{campaign_id}.jsonl", "a") as log_file:
        log_file.write(json.dumps(request.payload, ensure_ascii=False) + "\n")

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

    update_progress(campaign_id, user_id, tasks_data, progress_data, request.item_i, request.payload)
    save_progress_data(progress_data)

    return JSONResponse(content={"status": "ok"}, status_code=200)


class NextItemRequest(BaseModel):
    campaign_id: str
    user_id: str


@app.post("/get-next-item")
async def _get_next_item(request: NextItemRequest):
    campaign_id = request.campaign_id
    user_id = request.user_id

    if campaign_id not in progress_data:
        return JSONResponse(content={"error": "Unknown campaign ID"}, status_code=400)
    if user_id not in progress_data[campaign_id]:
        return JSONResponse(content={"error": "Unknown user ID"}, status_code=400)

    return get_next_item(
        campaign_id,
        user_id,
        tasks_data,
        progress_data,
    )


class DashboardDataRequest(BaseModel):
    campaign_id: str
    token: str | None = None


@app.post("/dashboard-data")
async def _dashboard_data(request: DashboardDataRequest):
    campaign_id = request.campaign_id

    is_privileged = (request.token == tasks_data[campaign_id]["token"])

    if campaign_id not in progress_data:
        return JSONResponse(content={"error": "Unknown campaign ID"}, status_code=400)

    progress_new = {}
    assignment = tasks_data[campaign_id]["info"]["assignment"]
    if assignment not in ["task-based", "single-stream"]:
        return JSONResponse(content={"error": "Unsupported campaign assignment type"}, status_code=400)

    for user_id, user_val in progress_data[campaign_id].items():
        # shallow copy
        entry = dict(user_val)

        if not is_privileged:
            entry["token_correct"] = None
            entry["token_incorrect"] = None

        progress_new[user_id] = entry

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
async def _reset_task(request: ResetTaskRequest):
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

    response = reset_task(campaign_id, user_id, tasks_data, progress_data)
    save_progress_data(progress_data)
    return response


@app.get("/download-annotations")
async def _download_annotations(
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
async def _download_progress(
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

static_dir = f"{os.path.dirname(os.path.abspath(__file__))}/static/"
if not os.path.exists(static_dir + "index.html"):
    raise FileNotFoundError("Static directory not found. Please build the frontend first.")

app.mount(
    "/",
    StaticFiles(directory=static_dir, html=True, follow_symlink=True),
    name="static",
)