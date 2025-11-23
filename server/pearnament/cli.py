import argparse

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
    args = argparse.ArgumentParser()
    args.add_argument('data_file', type=str, help='Path to the campaign data file')
    args.add_argument("-o", "--overwrite", action="store_true", help="Overwrite existing campaign if it exists")
    args = args.parse_args(args_unknown)

    import argparse
    import json
    import os
    import contextlib
    import wonderwords

    args = argparse.ArgumentParser()
    args.add_argument('data_file', type=str, help='Path to the campaign data file')
    args.add_argument("-o", "--overwrite", action="store_true", help="Overwrite existing campaign if it exists")
    parsed_args = args.parse_args()

    with open(parsed_args.data_file, 'r') as f:
        campaign_data = json.load(f)

    with contextlib.chdir(os.path.dirname(os.path.abspath(__file__))):
        with open("data/progress.json", "r") as f:
            progress_data = json.load(f)

        if campaign_data['campaign_id'] in progress_data and not parsed_args.overwrite:
            print(f"Campaign {campaign_data['campaign_id']} already exists. Use -o to overwrite.")
            exit(1)

        with open(f"data/{campaign_data['campaign_id']}.json", "w") as f:
            json.dump(progress_data, f, indent=2)

        if campaign_data["protocol"] in {"ESA", "MQM", "DA"}:
            # generate user mapping for task-based protocols
            pass
        else:
            # for dynamic protocols
            raise NotImplementedError("Only task-based protocols are supported for now.")

        progress_data[campaign_data['campaign_id']] = {
            "protocol": campaign_data["protocol"],
            "meta": campaign_data["meta"],
            "progress": users,
        }
    

def main():
    args = argparse.ArgumentParser()
    args.add_argument('command', type=str, help='Command to run', choices=['run', 'add'])
    args, args_unknown = args.parse_known_args()

    if args.command == 'run':
        _run()
    elif args.command == 'add':
        _add_campaign(args_unknown)

    print("running cli::main")
    pass