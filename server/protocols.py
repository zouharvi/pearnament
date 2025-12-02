import random
from typing import Any

from fastapi.responses import JSONResponse


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
        return get_next_item_single_stream(campaign_id, user_id, tasks_data, progress_data)
    elif assignment == "dynamic":
        return get_next_item_dynamic(campaign_id, user_id, tasks_data, progress_data)
    else:
        return JSONResponse(content={"error": "Unknown campaign assignment type"}, status_code=400)


def get_next_item_taskbased(
    campaign_id: str,
    user_id: str,
    data_all: dict,
    progress_data: dict,
) -> JSONResponse:
    """
    Get the next item for task-based protocol.
    """
    if all(progress_data[campaign_id][user_id]["progress"]):
        # all items completed
        # TODO: add check for data quality
        is_ok = True
        return JSONResponse(
            content={
                "status": "completed",
                "progress": {
                    "completed": sum(progress_data[campaign_id][user_id]["progress"]),
                    "time": progress_data[campaign_id][user_id]["time"],
                    "total": len(data_all[campaign_id]["data"][user_id]),
                    "array": progress_data[campaign_id][user_id]["progress"],
                },
                "token":  progress_data[campaign_id][user_id]["token_correct" if is_ok else "token_incorrect"],
            },
            status_code=200
        )

    # find first incomplete item
    item_i = min([i for i, v in enumerate(progress_data[campaign_id][user_id]["progress"]) if not v])
    return JSONResponse(
        content={
            "status": "ok",
            "progress": {
                "completed": sum(progress_data[campaign_id][user_id]["progress"]),
                "time": progress_data[campaign_id][user_id]["time"],
                "total": len(data_all[campaign_id]["data"][user_id]),
                "array": progress_data[campaign_id][user_id]["progress"],
            },
            "info": {
                "instructions": data_all[campaign_id]["info"].get("instructions", ""),
                "item_i": item_i,
            } | {
                k: v
                for k, v in data_all[campaign_id]["info"].items()
                if k.startswith("protocol")
            },
            "payload": data_all[campaign_id]["data"][user_id][item_i]},
        status_code=200
    )


def get_next_item_dynamic(campaign_data: dict, user_id: str, progress_data: dict, data_all: dict):
    raise NotImplementedError("Dynamic protocol is not implemented yet.")


def get_next_item_single_stream(
    campaign_id: str,
    user_id: str,
    data_all: dict,
    progress_data: dict,
) -> JSONResponse:
    """
    Get the next item for single-stream protocol.
    In this mode, all users share the same pool of items.
    Items are randomly selected from unfinished items.
    
    Note: There is a potential race condition where multiple users could
    receive the same item simultaneously. This is acceptable for this simple
    assignment type - the random selection minimizes collision probability.
    """
    # Get the shared progress array (stored at campaign level)
    shared_progress = progress_data[campaign_id]["_shared"]["progress"]
    total = len(shared_progress)
    completed = sum(shared_progress)

    if all(shared_progress):
        # all items completed
        # TODO: add check for data quality
        is_ok = True
        return JSONResponse(
            content={
                "status": "completed",
                "progress": {
                    "completed": completed,
                    "time": progress_data[campaign_id][user_id]["time"],
                    "total": total,
                    "array": shared_progress,
                },
                "token": progress_data[campaign_id][user_id]["token_correct" if is_ok else "token_incorrect"],
            },
            status_code=200
        )

    # find a random incomplete item
    incomplete_indices = [i for i, v in enumerate(shared_progress) if not v]
    item_i = random.choice(incomplete_indices)

    return JSONResponse(
        content={
            "status": "ok",
            "progress": {
                "completed": completed,
                "time": progress_data[campaign_id][user_id]["time"],
                "total": total,
                "array": shared_progress,
            },
            "info": {
                "instructions": data_all[campaign_id]["info"].get("instructions", ""),
                "item_i": item_i,
            } | {
                k: v
                for k, v in data_all[campaign_id]["info"].items()
                if k.startswith("protocol")
            },
            "payload": data_all[campaign_id]["data"][item_i]},
        status_code=200
    )


def reset_task(
    campaign_id: str,
    user_id: str,
    tasks_data: dict,
    progress_data: dict,
) -> JSONResponse:
    """
    Reset the task progress for the user in the specified campaign.
    """
    assignment = tasks_data[campaign_id]["info"]["assignment"]
    if assignment == "task-based":
        progress_data[campaign_id][user_id]["progress"] = [False]*len(tasks_data[campaign_id]["data"][user_id])
        progress_data[campaign_id][user_id]["time"] = 0.0
        progress_data[campaign_id][user_id]["time_start"] = None
        progress_data[campaign_id][user_id]["time_end"] = None
        return JSONResponse(content={"status": "ok"}, status_code=200)
    elif assignment == "single-stream":
        # For single-stream, only reset user's time (shared progress stays)
        progress_data[campaign_id][user_id]["time"] = 0.0
        progress_data[campaign_id][user_id]["time_start"] = None
        progress_data[campaign_id][user_id]["time_end"] = None
        return JSONResponse(content={"status": "ok"}, status_code=200)
    else:
        progress_data[campaign_id][user_id]["progress"] = []
        progress_data[campaign_id][user_id]["time"] = 0.0
        progress_data[campaign_id][user_id]["time_start"] = None
        progress_data[campaign_id][user_id]["time_end"] = None
        return JSONResponse(content={"status": "ok"}, status_code=200)
    


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
        # TODO: log attention checks/quality?
        return JSONResponse(content={"status": "ok"}, status_code=200)
    elif assignment == "single-stream":
        # Mark item as done in shared progress
        progress_data[campaign_id]["_shared"]["progress"][item_i] = True
        return JSONResponse(content={"status": "ok"}, status_code=200)
    elif assignment == "dynamic":
        return JSONResponse(content={"status": "error", "message": "Dynamic protocol logging not implemented yet."}, status_code=400)
    else:
        return JSONResponse(content={"status": "error", "message": "Unknown campaign assignment type"}, status_code=400)