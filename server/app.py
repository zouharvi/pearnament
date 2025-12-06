import json
import os
from typing import Any

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .assignment import get_i_item, get_next_item, reset_task, update_progress
from .utils import (
    ROOT,
    check_validation_threshold,
    get_db_log_item,
    load_progress_data,
    save_db_payload,
    save_progress_data,
)

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
    payload: dict[str, Any]


@app.post("/log-response")
async def _log_response(request: LogResponseRequest):
    global progress_data

    campaign_id = request.campaign_id
    user_id = request.user_id
    item_i = request.item_i

    if campaign_id not in progress_data:
        return JSONResponse(content="Unknown campaign ID", status_code=400)
    if user_id not in progress_data[campaign_id]:
        return JSONResponse(content="Unknown user ID", status_code=400)

    # append response to the output log
    save_db_payload(
        campaign_id, request.payload | {"user_id": user_id, "item_i": item_i})

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

    # Initialize validation_checks if it doesn't exist
    if "validations" in request.payload:
        if "validations" not in progress_data[campaign_id][user_id]:
            progress_data[campaign_id][user_id]["validations"] = {}

        progress_data[campaign_id][user_id]["validations"][request.item_i] = request.payload["validations"]

    update_progress(campaign_id, user_id, tasks_data,
                    progress_data, request.item_i, request.payload)
    save_progress_data(progress_data)

    return JSONResponse(content="ok", status_code=200)


class NextItemRequest(BaseModel):
    campaign_id: str
    user_id: str


@app.post("/get-next-item")
async def _get_next_item(request: NextItemRequest):
    campaign_id = request.campaign_id
    user_id = request.user_id

    if campaign_id not in progress_data:
        return JSONResponse(content="Unknown campaign ID", status_code=400)
    if user_id not in progress_data[campaign_id]:
        return JSONResponse(content="Unknown user ID", status_code=400)

    return get_next_item(
        campaign_id,
        user_id,
        tasks_data,
        progress_data,
    )


class GetItemRequest(BaseModel):
    campaign_id: str
    user_id: str
    item_i: int


@app.post("/get-i-item")
async def _get_i_item(request: GetItemRequest):
    campaign_id = request.campaign_id
    user_id = request.user_id
    item_i = request.item_i

    if campaign_id not in progress_data:
        return JSONResponse(content="Unknown campaign ID", status_code=400)
    if user_id not in progress_data[campaign_id]:
        return JSONResponse(content="Unknown user ID", status_code=400)

    return get_i_item(
        campaign_id,
        user_id,
        tasks_data,
        progress_data,
        item_i,
    )


class DashboardDataRequest(BaseModel):
    campaign_id: str
    token: str | None = None


@app.post("/dashboard-data")
async def _dashboard_data(request: DashboardDataRequest):
    campaign_id = request.campaign_id

    if campaign_id not in progress_data:
        return JSONResponse(content="Unknown campaign ID", status_code=400)
    
    is_privileged = (request.token == tasks_data[campaign_id]["token"])

    progress_new = {}
    assignment = tasks_data[campaign_id]["info"]["assignment"]
    if assignment not in ["task-based", "single-stream"]:
        return JSONResponse(content="Unsupported campaign assignment type", status_code=400)

    # Get threshold info for the campaign
    validation_threshold = tasks_data[campaign_id]["info"].get("validation_threshold")

    for user_id, user_val in progress_data[campaign_id].items():
        # shallow copy
        entry = dict(user_val)
        entry["validations"] = [
            all(v)
            for v in list(entry.get("validations", {}).values())
        ]
        
        # Add threshold pass/fail status (only when user is complete)
        if all(entry["progress"]):
            entry["threshold_passed"] = check_validation_threshold(
                tasks_data, progress_data, campaign_id, user_id
            )
        else:
            entry["threshold_passed"] = None

        if not is_privileged:
            entry["token_correct"] = None
            entry["token_incorrect"] = None

        progress_new[user_id] = entry

    return JSONResponse(
        content={
            "data": progress_new,
            "validation_threshold": validation_threshold
        },
        status_code=200
    )


class DashboardResultsRequest(BaseModel):
    campaign_id: str
    token: str


@app.post("/dashboard-results")
async def _dashboard_results(request: DashboardResultsRequest):
    campaign_id = request.campaign_id
    token = request.token

    if campaign_id not in progress_data:
        return JSONResponse(content="Unknown campaign ID", status_code=400)
    
    # Check if token is valid
    if token != tasks_data[campaign_id]["token"]:
        return JSONResponse(content="Invalid token", status_code=400)

    # Compute model scores from annotations
    model_scores = {}
    model_counts = {}
    
    # Iterate through all tasks to find items with 'model' field
    task_data = tasks_data[campaign_id]
    
    # Get all annotations for this campaign
    for user_id in progress_data[campaign_id].keys():
        user_progress = progress_data[campaign_id][user_id]["progress"]
        
        # Get assignment type
        assignment = task_data["info"]["assignment"]
        
        if assignment == "task-based":
            # task_data["data"] is a dict with user_id as key
            if user_id not in task_data["data"]:
                continue
            user_task_data = task_data["data"][user_id]
        elif assignment == "single-stream":
            user_task_data = task_data["data"]
        else:
            continue
        
        # Iterate through items
        for item_i, is_complete in enumerate(user_progress):
            if not is_complete:
                continue
                
            # Get annotations for this item
            annotations_list = get_db_log_item(campaign_id, user_id, item_i)
            
            # Get the actual item data
            if item_i >= len(user_task_data):
                continue
            
            doc_group = user_task_data[item_i]
            
            # Get the latest annotation for this item
            if not annotations_list:
                continue
            
            latest_annotation = annotations_list[-1]  # Take the most recent annotation
            if "annotations" not in latest_annotation:
                continue
            
            annotation_scores = latest_annotation["annotations"]
            
            # Match annotations to documents
            for doc_idx, doc in enumerate(doc_group):
                if doc_idx >= len(annotation_scores):
                    break
                
                annotation = annotation_scores[doc_idx]
                if not isinstance(annotation, dict) or "score" not in annotation:
                    continue
                
                score = annotation["score"]
                if score is None:
                    continue
                
                # Validate score is numeric
                if not isinstance(score, (int, float)):
                    continue
                
                # Check if this doc has a model field
                if "model" in doc:
                    model = doc["model"]
                    if model not in model_scores:
                        model_scores[model] = 0
                        model_counts[model] = 0
                    model_scores[model] += score
                    model_counts[model] += 1
    
    # Calculate averages and create ranking
    results = []
    for model in model_scores:
        if model_counts[model] > 0:
            avg_score = model_scores[model] / model_counts[model]
            results.append({
                "model": model,
                "avg_score": round(avg_score, 2),
                "count": model_counts[model]
            })
    
    # Sort by average score (descending)
    results.sort(key=lambda x: x["avg_score"], reverse=True)
    
    # Add rank
    for i, result in enumerate(results):
        result["rank"] = i + 1
    
    return JSONResponse(content={"results": results}, status_code=200)


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
        return JSONResponse(content="Unknown campaign ID", status_code=400)
    if token != tasks_data[campaign_id]["token"]:
        return JSONResponse(content="Invalid token", status_code=400)
    if user_id not in progress_data[campaign_id]:
        return JSONResponse(content="Unknown user ID", status_code=400)

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
            return JSONResponse(content=f"Unknown campaign ID {campaign_id}", status_code=400)
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
        return JSONResponse(content="Mismatched campaign_id and token count", status_code=400)

    output = {}
    for i, cid in enumerate(campaign_id):
        if cid not in progress_data:
            return JSONResponse(content=f"Unknown campaign ID {cid}", status_code=400)
        if token[i] != tasks_data[cid]["token"]:
            return JSONResponse(content=f"Invalid token for campaign ID {cid}", status_code=400)

        output[cid] = progress_data[cid]

    return JSONResponse(content=output, status_code=200)

static_dir = f"{os.path.dirname(os.path.abspath(__file__))}/static/"
if not os.path.exists(static_dir + "index.html"):
    raise FileNotFoundError(
        "Static directory not found. Please build the frontend first.")

app.mount(
    "/",
    StaticFiles(directory=static_dir, html=True, follow_symlink=True),
    name="static",
)
