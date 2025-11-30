from typing import Any

from fastapi.responses import JSONResponse


def get_next_item(
    campaign_id: str,
    user_id: str,
    tasks_data: dict,
    progress_data: dict,
) -> JSONResponse:
    if tasks_data[campaign_id]["info"]["type"] == "task-based":
        return get_next_item_taskbased(campaign_id, user_id, tasks_data, progress_data)
    elif tasks_data[campaign_id]["info"]["type"] == "dynamic":
        return get_next_item_dynamic(campaign_id, user_id, tasks_data, progress_data)
    else:
        return JSONResponse(content={"error": "Unknown campaign type"}, status_code=400)


def get_next_item_taskbased(
    campaign_id: str,
    user_id: str,
    data_all: dict,
    progress_data: dict,
) -> JSONResponse:
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
            },
            "info": {
                "status_message": data_all[campaign_id]["info"].get("status_message", ""),
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
    pass


def reset_task(
    campaign_id: str,
    user_id: str,
    tasks_data: dict,
    progress_data: dict,
) -> JSONResponse:
    if tasks_data[campaign_id]["info"]["type"] == "task-based":
        progress_data[campaign_id][user_id]["progress"] = [False]*len(tasks_data[campaign_id]["data"][user_id])
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
    


def log_response(
    campaign_id: str,
    user_id: str,
    tasks_data: dict,
    progress_data: dict,
    item_i: int,
    payload: Any,
) -> JSONResponse:
    if tasks_data[campaign_id]["info"]["type"] == "task-based":
        # even if it's already set it should be fine
        progress_data[campaign_id][user_id]["progress"][item_i] = True
        return JSONResponse(content={"status": "ok"}, status_code=200)
    elif tasks_data[campaign_id]["info"]["type"] == "dynamic":
        return JSONResponse(content={"status": "error", "message": "Dynamic protocol logging not implemented yet."}, status_code=400)
    elif tasks_data[campaign_id]["info"]["type"] == "task-single":
        return JSONResponse(content={"status": "error", "message": "Task-single protocol logging not implemented yet."}, status_code=400)
    else:
        return JSONResponse(content={"status": "error", "message": "Unknown campaign type"}, status_code=400)