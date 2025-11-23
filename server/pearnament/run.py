from typing import Any
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from .protocols import get_next_item_taskbased, get_next_item_dynamic
import json
from .utils import ROOT
import os
os.makedirs("data/outputs", exist_ok=True)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

data_all = {}

with open("data/progress.json", "r") as f:
    progress_data = json.load(f)


@app.post("/log-response")
async def log_response(campaign_id: str, user_id: str, payload: Any):
    global progress_data

    if campaign_id not in progress_data:
        return JSONResponse(content={"error": "Unknown campaign ID"}, status_code=400)
    if user_id not in progress_data[campaign_id]:
        return JSONResponse(content={"error": "Unknown user ID"}, status_code=400)
    
    with open(f"{ROOT}/data/outputs/{campaign_id}.jsonl", "a") as log_file:
        log_file.write(payload + "\n")
    
    progress_data[campaign_id][user_id] += 1


class NextItemRequest(BaseModel):
    campaign_id: str
    user_id: str

@app.post("/get-next-item")
async def get_next_item(item_request: NextItemRequest):
    campaign_id = item_request.campaign_id
    user_id = item_request.user_id

    if campaign_id not in progress_data:
        return JSONResponse(content={"error": "Unknown campaign ID"}, status_code=400)
    if user_id not in progress_data[campaign_id]:
        print(progress_data[campaign_id])
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