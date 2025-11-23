from fastapi.responses import JSONResponse
import hashlib

def get_next_item_taskbased(
        campaign_id: str,
        user_id: str,
        data_all: dict,
        progress_data: dict,
    ):
    if len(data_all[campaign_id]["data"][user_id]) == progress_data[campaign_id][user_id]:
        # TODO: add check for completion
        is_ok = True
        return JSONResponse(
            content={
                "status": "done",
                # vendor can verify the token to ensure the integrity of the completion status
                "token": hashlib.sha256(f"{campaign_id}|{user_id}|{is_ok}".encode()).hexdigest()
            },
            status_code=200
        )

    return JSONResponse(
        content={
            "status": "ok",
            "payload": data_all[campaign_id][user_id][progress_data[campaign_id][user_id]+1]},
            status_code=200
        )

def get_next_item_dynamic(campaign_data: dict, user_id: str, progress_data: dict, data_all: dict):
    pass