from fastapi.responses import JSONResponse

def get_next_item_taskbased(
        campaign_id: str,
        user_id: str,
        data_all: dict,
        progress_data: dict,
    ):
    if len(data_all[campaign_id]["data"][user_id]) == progress_data[campaign_id][user_id]["progress"]:
        # TODO: add check for data quality
        is_ok = True
        return JSONResponse(
            content={
                "status": "completed",
                "progress": {
                    "completed": progress_data[campaign_id][user_id]["progress"],
                    "time": progress_data[campaign_id][user_id]["time"],
                    "total": len(data_all[campaign_id]["data"][user_id]),
                },
                "token":  progress_data[campaign_id][user_id]["token_correct" if is_ok else  "token_incorrect"], 
            },
            status_code=200
        )

    return JSONResponse(
        content={
            "status": "ok",
            "progress": {
                "completed": progress_data[campaign_id][user_id]["progress"],
                "time": progress_data[campaign_id][user_id]["time"],
                "total": len(data_all[campaign_id]["data"][user_id]),
            },
            "info": {
                "status_message": data_all[campaign_id]["info"].get("status_message", ""),
            } | {
                k: v
                for k, v in data_all[campaign_id]["info"].items()
                if k.startswith("protocol")
            },
            "payload": data_all[campaign_id]["data"][user_id][progress_data[campaign_id][user_id]["progress"]]},
            status_code=200
        )

def get_next_item_dynamic(campaign_data: dict, user_id: str, progress_data: dict, data_all: dict):
    raise NotImplementedError("Dynamic protocol is not implemented yet.")
    pass