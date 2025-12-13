import random
from typing import Any

from fastapi.responses import JSONResponse

from .utils import (
    RESET_MARKER,
    check_validation_threshold,
    get_db_log,
    get_db_log_item,
    save_db_payload,
)


def _completed_response(
    tasks_data: dict,
    progress_data: dict,
    campaign_id: str,
    user_id: str,
) -> JSONResponse:
    """Build a completed response with progress, time, and token."""
    user_progress = progress_data[campaign_id][user_id]
    is_ok = check_validation_threshold(tasks_data, progress_data, campaign_id, user_id)
    return JSONResponse(
        content={
            "status": "completed",
            "progress": user_progress["progress"],
            "time": user_progress["time"],
            "token": user_progress["token_correct" if is_ok else "token_incorrect"],
        },
        status_code=200
    )


def get_next_item(
    campaign_id: str,
    user_id: str,
    tasks_data: dict,
    progress_data: dict,
) -> JSONResponse:
    """
    Get the next item for the user in the specified campaign.
    """
    assignment = tasks_data[campaign_id]["info"]["assignment"]
    if assignment == "task-based":
        return get_next_item_taskbased(campaign_id, user_id, tasks_data, progress_data)
    elif assignment == "single-stream":
        return get_next_item_singlestream(campaign_id, user_id, tasks_data, progress_data)
    elif assignment == "dynamic":
        return get_next_item_dynamic(campaign_id, user_id, tasks_data, progress_data)
    else:
        return JSONResponse(content="Unknown campaign assignment type", status_code=400)


def get_i_item(
    campaign_id: str,
    user_id: str,
    tasks_data: dict,
    progress_data: dict,
    item_i: int,
) -> JSONResponse:
    """
    Get a specific item by index for the user in the specified campaign.
    """
    assignment = tasks_data[campaign_id]["info"]["assignment"]
    if assignment == "task-based":
        return get_i_item_taskbased(campaign_id, user_id, tasks_data, progress_data, item_i)
    elif assignment in ["single-stream", "dynamic"]:
        return get_i_item_singlestream(campaign_id, user_id, tasks_data, progress_data, item_i)
    else:
        return JSONResponse(content="Get item not supported for this assignment type", status_code=400)


def get_i_item_taskbased(
    campaign_id: str,
    user_id: str,
    data_all: dict,
    progress_data: dict,
    item_i: int,
) -> JSONResponse:
    """
    Get specific item for task-based protocol.
    """
    user_progress = progress_data[campaign_id][user_id]

    # try to get existing annotations if any
    items_existing = get_db_log_item(campaign_id, user_id, item_i)
    payload_existing = None
    if items_existing:
        # get the latest ones
        latest_item = items_existing[-1]
        payload_existing = {"annotation": latest_item["annotation"]}
        if "comment" in latest_item:
            payload_existing["comment"] = latest_item["comment"]

    if item_i < 0 or item_i >= len(data_all[campaign_id]["data"][user_id]):
        return JSONResponse(
            content="Item index out of range",
            status_code=400
        )

    return JSONResponse(
        content={
            "status": "ok",
            "progress": user_progress["progress"],
            "time": user_progress["time"],
            "info": {
                "item_i": item_i,
            } | {
                k: v
                for k, v in data_all[campaign_id]["info"].items()
                if k.startswith("protocol")
            },
            "payload": data_all[campaign_id]["data"][user_id][item_i]
        } | ({"payload_existing": payload_existing} if payload_existing else {}),
        status_code=200
    )


def get_i_item_singlestream(
    campaign_id: str,
    user_id: str,
    data_all: dict,
    progress_data: dict,
    item_i: int,
) -> JSONResponse:
    """
    Get specific item for single-stream assignment.
    """
    user_progress = progress_data[campaign_id][user_id]

    # try to get existing annotations if any
    # note the None user_id since it is shared
    items_existing = get_db_log_item(campaign_id, None, item_i)
    payload_existing = None
    if items_existing:
        # get the latest ones
        latest_item = items_existing[-1]
        payload_existing = {"annotation": latest_item["annotation"]}
        if "comment" in latest_item:
            payload_existing["comment"] = latest_item["comment"]

    if item_i < 0 or item_i >= len(data_all[campaign_id]["data"]):
        return JSONResponse(
            content="Item index out of range",
            status_code=400
        )

    return JSONResponse(
        content={
            "status": "ok",
            "progress": user_progress["progress"],
            "time": user_progress["time"],
            "info": {
                "item_i": item_i,
            } | {
                k: v
                for k, v in data_all[campaign_id]["info"].items()
                if k.startswith("protocol")
            },
            "payload": data_all[campaign_id]["data"][item_i]
        } | ({"payload_existing": payload_existing} if payload_existing else {}),
        status_code=200
    )


def get_next_item_taskbased(
    campaign_id: str,
    user_id: str,
    data_all: dict,
    progress_data: dict,
) -> JSONResponse:
    """
    Get the next item for task-based assignment.
    """
    user_progress = progress_data[campaign_id][user_id]
    if all(user_progress["progress"]):
        return _completed_response(data_all, progress_data, campaign_id, user_id)

    # find first incomplete item
    item_i = min([i for i, v in enumerate(user_progress["progress"]) if not v])

    # try to get existing annotations if any
    items_existing = get_db_log_item(campaign_id, user_id, item_i)
    payload_existing = None
    if items_existing:
        # get the latest ones
        latest_item = items_existing[-1]
        payload_existing = {"annotation": latest_item["annotation"]}
        if "comment" in latest_item:
            payload_existing["comment"] = latest_item["comment"]

    return JSONResponse(
        content={
            "status": "ok",
            "progress": user_progress["progress"],
            "time": user_progress["time"],
            "info": {
                "item_i": item_i,
            } | {
                k: v
                for k, v in data_all[campaign_id]["info"].items()
                if k.startswith("protocol")
            },
            "payload": data_all[campaign_id]["data"][user_id][item_i]
        } | ({"payload_existing": payload_existing} if payload_existing else {}),
        status_code=200
    )


def get_next_item_singlestream(
    campaign_id: str,
    user_id: str,
    data_all: dict,
    progress_data: dict,
) -> JSONResponse:
    """
    Get the next item for single-stream assignment.
    In this mode, all users share the same pool of items.
    Items are randomly selected from unfinished items.

    Note: There is a potential race condition where multiple users could
    receive the same item simultaneously. This is fine since we store all responses.
    """
    user_progress = progress_data[campaign_id][user_id]
    progress = user_progress["progress"]

    if all(progress):
        return _completed_response(data_all, progress_data, campaign_id, user_id)

    # find a random incomplete item
    incomplete_indices = [i for i, v in enumerate(progress) if not v]
    item_i = random.choice(incomplete_indices)

    # try to get existing annotations if any
    # note the None user_id since it is shared
    items_existing = get_db_log_item(campaign_id, None, item_i)
    payload_existing = None
    if items_existing:
        # get the latest ones
        latest_item = items_existing[-1]
        payload_existing = {"annotation": latest_item["annotation"]}
        if "comment" in latest_item:
            payload_existing["comment"] = latest_item["comment"]

    return JSONResponse(
        content={
            "status": "ok",
            "time": user_progress["time"],
            "progress": progress,
            "info": {
                "item_i": item_i,
            } | {
                k: v
                for k, v in data_all[campaign_id]["info"].items()
                if k.startswith("protocol")
            },
            "payload": data_all[campaign_id]["data"][item_i]
        } | ({"payload_existing": payload_existing} if payload_existing else {}),
        status_code=200
    )



def get_next_item_dynamic(
    campaign_id: str,
    user_id: str,
    tasks_data: dict,
    progress_data: dict,
) -> JSONResponse:
    """
    Get the next item for dynamic assignment based on model performance.
    
    In this mode, items are selected based on the current performance of models:
    1. First, each model gets `dynamic_first` items for baseline evaluation
    2. After that, items are selected from top `dynamic_top` performing models
    3. With probability `dynamic_backoff`, uniformly random selection is used instead
    """
    import random
    
    user_progress = progress_data[campaign_id][user_id]
    campaign_data = tasks_data[campaign_id]
    
    # Check if completed
    if all(user_progress["progress"]):
        return _completed_response(tasks_data, progress_data, campaign_id, user_id)
    
    # Get configuration parameters
    dynamic_top = campaign_data["info"].get("dynamic_top", 1)
    dynamic_first = campaign_data["info"].get("dynamic_first", 0)
    dynamic_backoff = campaign_data["info"].get("dynamic_backoff", 0)
    
    # Get all unique models in the campaign
    all_models = set()
    for item in campaign_data["data"]:
        if item and len(item) > 0:
            all_models.update(item[0]["tgt"].keys())
    
    # Count annotations per model to determine if we're in the first phase
    annotations = get_db_log(campaign_id)
    model_annotation_counts = {}
    for annotation in annotations:
        if "annotation" not in annotation:
            continue
        ann_data = annotation.get("annotation", {})
        if not isinstance(ann_data, dict):
            continue
        # Count annotations for each model in this item
        item_i = annotation.get("item_i")
        if item_i is not None and item_i < len(campaign_data["data"]):
            item = campaign_data["data"][item_i]
            if item and len(item) > 0:
                for model_name in item[0]["tgt"].keys():
                    model_annotation_counts[model_name] = model_annotation_counts.get(model_name, 0) + 1
    
    # Check if we're still in the first phase (collecting initial data)
    in_first_phase = any(model_annotation_counts.get(model, 0) < dynamic_first for model in all_models)
    
    # Determine which models to sample from
    if in_first_phase or random.random() < dynamic_backoff:
        # Sample uniformly from incomplete items
        incomplete_indices = [i for i, v in enumerate(user_progress["progress"]) if not v]
        item_i = random.choice(incomplete_indices)
    else:
        # Calculate model scores from annotations
        model_scores = {}
        for annotation in annotations:
            if "annotation" not in annotation:
                continue
            ann_data = annotation.get("annotation", {})
            if not isinstance(ann_data, dict):
                continue
            item_i_ann = annotation.get("item_i")
            if item_i_ann is not None and item_i_ann < len(campaign_data["data"]):
                item = campaign_data["data"][item_i_ann]
                if item and len(item) > 0:
                    # Get scores for each model in this annotation
                    for model_name in item[0]["tgt"].keys():
                        if model_name in ann_data:
                            model_ann = ann_data.get(model_name, {})
                            if isinstance(model_ann, dict) and "score" in model_ann:
                                score = model_ann["score"]
                                if model_name not in model_scores:
                                    model_scores[model_name] = []
                                model_scores[model_name].append(score)
        
        # Calculate average scores
        model_avg_scores = {
            model: sum(scores) / len(scores)
            for model, scores in model_scores.items()
            if len(scores) > 0
        }
        
        # Get top N models
        if model_avg_scores:
            sorted_models = sorted(model_avg_scores.items(), key=lambda x: x[1], reverse=True)
            top_models = set([model for model, score in sorted_models[:dynamic_top]])
        else:
            # If no scores yet, use all models
            top_models = all_models
        
        # Find incomplete items that contain at least one top model
        incomplete_indices = [
            i for i, v in enumerate(user_progress["progress"])
            if not v and any(
                model in top_models
                for model in campaign_data["data"][i][0]["tgt"].keys()
            )
        ]
        
        if not incomplete_indices:
            # Fallback to any incomplete item
            incomplete_indices = [i for i, v in enumerate(user_progress["progress"]) if not v]
        
        item_i = random.choice(incomplete_indices)
    
    # Try to get existing annotations if any
    # note the None user_id since items are shared in the pool
    items_existing = get_db_log_item(campaign_id, None, item_i)
    payload_existing = None
    if items_existing:
        latest_item = items_existing[-1]
        payload_existing = {"annotation": latest_item["annotation"]}
        if "comment" in latest_item:
            payload_existing["comment"] = latest_item["comment"]
    
    return JSONResponse(
        content={
            "status": "ok",
            "time": user_progress["time"],
            "progress": user_progress["progress"],
            "info": {
                "item_i": item_i,
            } | {
                k: v
                for k, v in campaign_data["info"].items()
                if k.startswith("protocol")
            },
            "payload": campaign_data["data"][item_i]
        } | ({"payload_existing": payload_existing} if payload_existing else {}),
        status_code=200
    )



def _reset_user_time(progress_data: dict, campaign_id: str, user_id: str) -> None:
    """Reset time tracking fields for a user."""
    progress_data[campaign_id][user_id]["time"] = 0.0
    progress_data[campaign_id][user_id]["time_start"] = None
    progress_data[campaign_id][user_id]["time_end"] = None
    progress_data[campaign_id][user_id]["validations"] = {}


def reset_task(
    campaign_id: str,
    user_id: str,
    tasks_data: dict,
    progress_data: dict,
) -> JSONResponse:
    """
    Reset the task progress for the user in the specified campaign.
    Saves a reset marker to mask existing annotations.
    """
    assignment = tasks_data[campaign_id]["info"]["assignment"]
    if assignment == "task-based":
        # Save reset marker for this user to mask existing annotations
        num_items = len(tasks_data[campaign_id]["data"][user_id])
        for item_i in range(num_items):
            save_db_payload(campaign_id, {
                "user_id": user_id,
                "item_i": item_i,
                "annotation": RESET_MARKER
            })
        progress_data[campaign_id][user_id]["progress"] = [False] * num_items
        _reset_user_time(progress_data, campaign_id, user_id)
        return JSONResponse(content="ok", status_code=200)
    elif assignment == "single-stream":
        # Save reset markers for all items (shared pool)
        num_items = len(tasks_data[campaign_id]["data"])
        for item_i in range(num_items):
            save_db_payload(campaign_id, {
                "user_id": None,
                "item_i": item_i,
                "annotation": RESET_MARKER
            })
        # for single-stream reset all progress
        for uid in progress_data[campaign_id]:
            progress_data[campaign_id][uid]["progress"] = [False] * num_items
        _reset_user_time(progress_data, campaign_id, user_id)
        return JSONResponse(content="ok", status_code=200)
    elif assignment == "dynamic":
        # Save reset markers for all items (shared pool like single-stream)
        num_items = len(tasks_data[campaign_id]["data"])
        for item_i in range(num_items):
            save_db_payload(campaign_id, {
                "user_id": None,
                "item_i": item_i,
                "annotation": RESET_MARKER
            })
        # for dynamic reset all progress
        for uid in progress_data[campaign_id]:
            progress_data[campaign_id][uid]["progress"] = [False] * num_items
        _reset_user_time(progress_data, campaign_id, user_id)
        return JSONResponse(content="ok", status_code=200)
    else:
        return JSONResponse(content="Reset not supported for this assignment type", status_code=400)


def update_progress(
    campaign_id: str,
    user_id: str,
    tasks_data: dict,
    progress_data: dict,
    item_i: int,
    payload: Any,
) -> JSONResponse:
    """
    Log the user's response for the specified item in the campaign.
    """
    assignment = tasks_data[campaign_id]["info"]["assignment"]
    if assignment == "task-based":
        # even if it's already set it should be fine
        progress_data[campaign_id][user_id]["progress"][item_i] = True
        return JSONResponse(content={"status": "ok"}, status_code=200)
    elif assignment == "single-stream":
        # progress all users
        for uid in progress_data[campaign_id]:
            progress_data[campaign_id][uid]["progress"][item_i] = True
        return JSONResponse(content="ok", status_code=200)
    elif assignment == "dynamic":
        # progress all users (shared pool like single-stream)
        for uid in progress_data[campaign_id]:
            progress_data[campaign_id][uid]["progress"][item_i] = True
        return JSONResponse(content="ok", status_code=200)
    else:
        return JSONResponse(content="Unknown campaign assignment type", status_code=400)
