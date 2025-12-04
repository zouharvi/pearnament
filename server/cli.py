"""
Command-line interface for managing and running the Pearmut server.
"""

import argparse
import hashlib
import json
import os
import urllib.parse

import psutil

from .utils import ROOT, load_progress_data, save_progress_data

os.makedirs(f"{ROOT}/data/tasks", exist_ok=True)
load_progress_data(warn=None)


def _run(args_unknown):
    import uvicorn

    from .app import app, tasks_data

    args = argparse.ArgumentParser()
    args.add_argument(
        "--port", type=int, default=8001,
        help="Port to run the server on"
    )
    args.add_argument(
        "--server", default="http://localhost:8001",
        help="Prefix server URL for protocol links"
    )
    args = args.parse_args(args_unknown)

    # print access dashboard URL for all campaigns
    if tasks_data:
        print(
            args.server + "/dashboard.html?" + "&".join([
                f"campaign_id={urllib.parse.quote_plus(campaign_id)}&token={campaign_data["token"]}"
                for campaign_id, campaign_data in tasks_data.items()
            ])
        )

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=args.port,
        reload=False,
        # log_level="info",
    )


def _add_single_campaign(data_file, overwrite, server):
    """
    Add a single campaign from a JSON data file.
    """
    import random

    import wonderwords

    with open(data_file, 'r') as f:
        campaign_data = json.load(f)

    with open(f"{ROOT}/data/progress.json", "r") as f:
        progress_data = json.load(f)

    if campaign_data['campaign_id'] in progress_data and not overwrite:
        print(
            f"Campaign {campaign_data['campaign_id']} already exists.",
            "Use -o to overwrite."
        )
        exit(1)

    if "info" not in campaign_data:
        raise ValueError("Campaign data must contain 'info' field.")
    if "data" not in campaign_data:
        raise ValueError("Campaign data must contain 'data' field.")
    if "assignment" not in campaign_data["info"]:
        raise ValueError("Campaign 'info' must contain 'assignment' field.")
    if "template" not in campaign_data["info"]:
        raise ValueError("Campaign 'info' must contain 'template' field.")

    assignment = campaign_data["info"]["assignment"]
    # use random words for identifying users
    rng = random.Random(campaign_data["campaign_id"])
    rword = wonderwords.RandomWord(rng=rng)

    # Parse users specification from info
    users_spec = campaign_data["info"].get("users")
    user_tokens = {}  # user_id -> {"pass": ..., "fail": ...}

    if assignment == "task-based":
        tasks = campaign_data["data"]
        if not isinstance(tasks, list):
            raise ValueError(
                "Task-based campaign 'data' must be a list of tasks.")
        if not all(isinstance(task, list) for task in tasks):
            raise ValueError(
                "Each task in task-based campaign 'data' must be a list of items.")
        num_users = len(tasks)
    elif assignment == "single-stream":
        tasks = campaign_data["data"]
        if users_spec is None:
            raise ValueError(
                "Single-stream campaigns must specify 'users' in info.")
        if not isinstance(campaign_data["data"], list):
            raise ValueError(
                "Single-stream campaign 'data' must be a list of items.")
        if isinstance(users_spec, int):
            num_users = users_spec
        elif isinstance(users_spec, list):
            num_users = len(users_spec)
        else:
            raise ValueError("'users' must be an integer or a list.")
    elif assignment == "dynamic":
        raise NotImplementedError(
            "Dynamic campaign assignment is not yet implemented.")
    else:
        raise ValueError(f"Unknown campaign assignment type: {assignment}")

    # Generate or parse user IDs based on users specification
    if users_spec is None or isinstance(users_spec, int):
        # Generate random user IDs
        user_ids = []
        while len(user_ids) < num_users:
            new_id = f"{rword.random_words(amount=1, include_parts_of_speech=['adjective'])[0]}-{rword.random_words(amount=1, include_parts_of_speech=['noun'])[0]}"
            if new_id not in user_ids:
                user_ids.append(new_id)
        user_ids = [
            f"{user_id}-{rng.randint(0, 999):03d}"
            for user_id in user_ids
        ]
    elif isinstance(users_spec, list):
        if len(users_spec) != num_users:
            raise ValueError(
                f"Number of users ({len(users_spec)}) must match expected count ({num_users}).")
        if all(isinstance(u, str) for u in users_spec):
            # List of string IDs
            user_ids = users_spec
        elif all(isinstance(u, dict) for u in users_spec):
            # List of dicts with user_id, token_pass, token_fail
            user_ids = []
            for u in users_spec:
                if "user_id" not in u:
                    raise ValueError("Each user dict must contain 'user_id'.")
                user_ids.append(u["user_id"])
                user_tokens[u["user_id"]] = {
                    "pass": u.get("token_pass"),
                    "fail": u.get("token_fail"),
                }
        else:
            raise ValueError("'users' list must contain all strings or all dicts.")
    else:
        raise ValueError("'users' must be an integer or a list.")

    # For task-based, data is a dict mapping user_id -> tasks
    # For single-stream, data is a flat list (shared among all users)
    if assignment == "task-based":
        campaign_data["data"] = {
            user_id: task
            for user_id, task in zip(user_ids, tasks)
        }
    elif assignment == "single-stream":
        campaign_data["data"] = tasks

    # generate a token for dashboard access if not present
    if "token" not in campaign_data:
        campaign_data["token"] = (
            hashlib.sha256(random.randbytes(16)).hexdigest()[:10]
        )

    def get_token(user_id, token_type):
        """Get user token or generate a random one."""
        token = user_tokens.get(user_id, {}).get(token_type)
        if token is not None:
            return token
        return hashlib.sha256(random.randbytes(16)).hexdigest()[:10]

    user_progress = {
        user_id: {
            # TODO: progress tracking could be based on the assignment type
            "progress": (
                [False]*len(campaign_data["data"][user_id]) if assignment == "task-based"
                else [False]*len(campaign_data["data"]) if assignment == "single-stream"
                else []
            ),
            "time_start": None,
            "time_end": None,
            "time": 0,
            "url": (
                f"{campaign_data["info"]["template"]}.html"
                f"?campaign_id={urllib.parse.quote_plus(campaign_data['campaign_id'])}"
                f"&user_id={user_id}"
            ),
            "token_correct": get_token(user_id, "pass"),
            "token_incorrect": get_token(user_id, "fail"),
        }
        for user_id in user_ids
    }

    with open(f"{ROOT}/data/tasks/{campaign_data['campaign_id']}.json", "w") as f:
        json.dump(campaign_data, f, indent=2, ensure_ascii=False)

    progress_data[campaign_data['campaign_id']] = user_progress

    with open(f"{ROOT}/data/progress.json", "w") as f:
        json.dump(progress_data, f, indent=2, ensure_ascii=False)

    print(
        f"{server}/dashboard.html"
        f"?campaign_id={urllib.parse.quote_plus(campaign_data['campaign_id'])}"
        f"&token={campaign_data['token']}"
    )
    print("-"*10)
    for user_id, user_val in user_progress.items():
        # point to the protocol URL
        print(f'{server}/{user_val["url"]}')


def _add_campaign(args_unknown):
    """
    Add campaigns from one or more JSON data files.
    """
    args = argparse.ArgumentParser()
    args.add_argument(
        'data_files', type=str, nargs='+',
        help='One or more paths to campaign data files'
    )
    args.add_argument(
        "-o", "--overwrite", action="store_true",
        help="Overwrite existing campaign if it exists"
    )
    args.add_argument(
        "--server", default="http://localhost:8001",
        help="Prefix server URL for protocol links"
    )
    args = args.parse_args(args_unknown)

    for data_file in args.data_files:
        try:
            _add_single_campaign(data_file, args.overwrite, args.server)
        except Exception as e:
            print(f"Error processing {data_file}: {e}")
            exit(1)


def main():
    """
    Main entry point for the CLI.
    """
    args = argparse.ArgumentParser()
    args.add_argument('command', type=str, choices=['run', 'add', 'purge'])
    args, args_unknown = args.parse_known_args()

    # enforce that only one pearmut process is running
    for p in psutil.process_iter():
        if "pearmut" == p.name() and p.pid != os.getpid():
            print("Exit all running pearmut processes before running more commands.")
            print(p)
            exit(1)

    if args.command == 'run':
        _run(args_unknown)
    elif args.command == 'add':
        _add_campaign(args_unknown)
    elif args.command == 'purge':
        import shutil

        # Parse optional campaign name
        purge_args = argparse.ArgumentParser()
        purge_args.add_argument(
            'campaign', type=str, nargs='?', default=None,
            help='Optional campaign name to purge (purges all if not specified)'
        )
        purge_args = purge_args.parse_args(args_unknown)

        if purge_args.campaign is not None:
            # Purge specific campaign
            campaign_id = purge_args.campaign
            confirm = input(
                f"Are you sure you want to purge campaign '{campaign_id}'? This action cannot be undone. [y/n] "
            )
            if confirm.lower() == 'y':
                # Remove task file
                task_file = f"{ROOT}/data/tasks/{campaign_id}.json"
                if os.path.exists(task_file):
                    os.remove(task_file)
                # Remove output file
                output_file = f"{ROOT}/data/outputs/{campaign_id}.jsonl"
                if os.path.exists(output_file):
                    os.remove(output_file)
                # Remove from progress data
                if os.path.exists(f"{ROOT}/data/progress.json"):
                    with open(f"{ROOT}/data/progress.json", "r") as f:
                        progress_data = json.load(f)
                    if campaign_id in progress_data:
                        del progress_data[campaign_id]
                        save_progress_data(progress_data)
                print(f"Campaign '{campaign_id}' purged.")
            else:
                print("Cancelled.")
        else:
            # Purge all campaigns
            confirm = input(
                "Are you sure you want to purge all campaign data? This action cannot be undone. [y/n] "
            )
            if confirm.lower() == 'y':
                shutil.rmtree(f"{ROOT}/data/tasks", ignore_errors=True)
                shutil.rmtree(f"{ROOT}/data/outputs", ignore_errors=True)
                if os.path.exists(f"{ROOT}/data/progress.json"):
                    os.remove(f"{ROOT}/data/progress.json")
                print("All campaign data purged.")
            else:
                print("Cancelled.")
