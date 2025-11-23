from fastapi.responses import JSONResponse

def get_next_item_taskbased(
        campaign_id: str,
        user_id: str,
        data_all: dict,
        progress_data: dict,
    ):
    if len(data_all[campaign_id]["data"][user_id]) == progress_data[campaign_id][user_id]:
        return JSONResponse(content={"status": "done", "key": "TODO"}, status_code=200)

    return JSONResponse(
        content={
            "status": "ok",
            "payload": data_all[campaign_id][user_id][progress_data[campaign_id][user_id]+1]},
            status_code=200
        )

def get_next_item_dynamic(campaign_data: dict, user_id: str, progress_data: dict, data_all: dict):
    pass