import argparse
import hashlib
import os
import urllib.parse

from .utils import ROOT

os.makedirs(f"{ROOT}/data/tasks", exist_ok=True)
if not os.path.exists(f"{ROOT}/data/progress.json"):
    with open(f"{ROOT}/data/progress.json", "w") as f:
        f.write("{}")


def _run():
    import uvicorn

    from .run import app
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8001,
        # reload=reload_enabled,
        # log_level="info",
        # app_dir="src",
        # factory=False # factory=False means it expects 'app' to be a variable
    )


def _add_campaign(args_unknown):
    import argparse
    import json
    import random

    import wonderwords

    args = argparse.ArgumentParser()
    args.add_argument('data_file', type=str,
                      help='Path to the campaign data file')
    args.add_argument("-o", "--overwrite", action="store_true",
                      help="Overwrite existing campaign if it exists")
    args = args.parse_args(args_unknown)

    with open(args.data_file, 'r') as f:
        campaign_data = json.load(f)

    with open(f"{ROOT}/data/progress.json", "r") as f:
        progress_data = json.load(f)

    if campaign_data['campaign_id'] in progress_data and not args.overwrite:
        print(
            f"Campaign {campaign_data['campaign_id']} already exists.",
            "Use -o to overwrite."
        )
        exit(1)

    # use random words for identifying users
    rng = random.Random(campaign_data["campaign_id"])
    rword = wonderwords.RandomWord(rng=rng)
    if campaign_data["info"]["type"] == "task-based":
        tasks = campaign_data["data"]
        amount = len(tasks)
    elif campaign_data["info"]["type"] == "dynamic":
        amount = campaign_data["num_users"]
    else:
        raise ValueError(
            f"Unknown campaign type: {campaign_data["info"]['type']}")

    user_ids = []
    while len(user_ids) < amount:
        new_id = f"{rword.random_words(amount=1, include_parts_of_speech=['adjective'])[0]}-{rword.random_words(amount=1, include_parts_of_speech=['noun'])[0]}"
        if new_id not in user_ids:
            user_ids.append(new_id)
    user_ids = [
        f"{user_id}-{rng.randint(0, 999):03d}"
        for user_id in user_ids
    ]

    server_url = campaign_data["info"].get(
        "url",
        "127.0.0.1:8001",  # by default local server
    ).removesuffix("/")

    campaign_data["data"] = {
        user_id: task
        for user_id, task in zip(user_ids, tasks)
    }
    user_progress = {
        user_id: {
            "progress": 0,
            "time_start": None,
            "time_end": None,
            "time": 0,
            "url": (
                f"{server_url}/{campaign_data["info"]["template"]}.html"
                f"?campaign_id={urllib.parse.quote_plus(campaign_data['campaign_id'])}"
                f"&user_id={user_id}"
            ),
            "token_correct": hashlib.sha256(random.randbytes(16)).hexdigest()[:16],
            "token_incorrect": hashlib.sha256(random.randbytes(16)).hexdigest()[:16],
        }
        for user_id in user_ids
    }

    with open(f"{ROOT}/data/tasks/{campaign_data['campaign_id']}.json", "w") as f:
        json.dump(campaign_data, f, indent=2)

    progress_data[campaign_data['campaign_id']] = user_progress

    with open(f"{ROOT}/data/progress.json", "w") as f:
        json.dump(progress_data, f, indent=2, ensure_ascii=False)

    print(
        f"{server_url}/dashboard.html"
        f"?campaign_id={urllib.parse.quote_plus(campaign_data['campaign_id'])}"
        f"&token=TODO"
    )
    print("-"*10)
    for user_id, user_val in user_progress.items():
        # point to the protocol URL
        print(user_val["url"])


def main():
    args = argparse.ArgumentParser()
    args.add_argument('command', type=str, choices=['run', 'add'])
    args, args_unknown = args.parse_known_args()

    if args.command == 'run':
        _run()
    elif args.command == 'add':
        _add_campaign(args_unknown)
