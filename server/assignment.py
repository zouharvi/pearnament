import random
from typing import Any

from fastapi.responses import JSONResponse

from .utils import (
    RESET_MARKER,
    check_validation_threshold,
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
    elif assignment == "single-stream":
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



def get_next_item_dynamic(campaign_data: dict, user_id: str, progress_data: dict, data_all: dict):
    raise NotImplementedError("Dynamic protocol is not implemented yet.")



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
        return JSONResponse(content="Dynamic protocol logging not implemented yet.", status_code=400)
    else:
        return JSONResponse(content="Unknown campaign assignment type", status_code=400)
