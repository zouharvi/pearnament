import json
import os

ROOT = "."


def highlight_differences(a, b):
    """
    Compares two strings and wraps their differences in HTML span tags.

    Args:
        a: The first string.
        b: The second string.

    Returns:
        A tuple containing the two strings with their differences highlighted.
    """
    import difflib
    # TODO: maybe on the level of words?
    s = difflib.SequenceMatcher(None, a, b)
    res_a, res_b = [], []
    span_open = '<span class="difference">'
    span_close = '</span>'

    for tag, i1, i2, j1, j2 in s.get_opcodes():
        if tag == 'equal' or (i2-i1 <= 2 and j2-j1 <= 2):
            res_a.append(a[i1:i2])
            res_b.append(b[j1:j2])
        else:
            if tag in ('replace', 'delete'):
                res_a.append(f"{span_open}{a[i1:i2]}{span_close}")
            if tag in ('replace', 'insert'):
                res_b.append(f"{span_open}{b[j1:j2]}{span_close}")

    return "".join(res_a), "".join(res_b)


def load_progress_data(warn: str | None = None):
    if not os.path.exists(f"{ROOT}/data/progress.json"):
        if warn is not None:
            print(warn)
        with open(f"{ROOT}/data/progress.json", "w") as f:
            f.write(json.dumps({}))
    with open(f"{ROOT}/data/progress.json", "r") as f:
        return json.load(f)


def save_progress_data(data):
    with open(f"{ROOT}/data/progress.json", "w") as f:
        json.dump(data, f, indent=2)


_logs = {}


def get_db_log(campaign_id: str) -> list[dict]:
    """
    Returns up to date log for the given campaign_id.
    """
    if campaign_id not in _logs:
        # create a new one if it doesn't exist
        log_path = f"{ROOT}/data/outputs/{campaign_id}.jsonl"
        if os.path.exists(log_path):
            with open(log_path, "r") as f:
                _logs[campaign_id] = [
                    json.loads(line) for line in f.readlines()
                ]
        else:
            _logs[campaign_id] = []

    return _logs[campaign_id]


def get_db_log_item(campaign_id: str, user_id: str | None, item_i: int | None) -> list[dict]:
    """
    Returns the log item for the given campaign_id, user_id and item_i.
    Can be empty.
    """
    log = get_db_log(campaign_id)
    return [
        entry for entry in log
        if (
            (user_id is None or entry.get("user_id") == user_id) and
            (item_i is None or entry.get("item_i") == item_i)
        )
    ]


def save_db_payload(campaign_id: str, payload: dict):
    """
    Saves the given payload to the log for the given campaign_id, user_id and item_i.
    Saves both on disk and in-memory.
    """

    log_path = f"{ROOT}/data/outputs/{campaign_id}.jsonl"
    with open(log_path, "a") as log_file:
        log_file.write(json.dumps(payload, ensure_ascii=False,) + "\n")

    log = get_db_log(campaign_id)
    # copy to avoid mutation issues
    log.append(payload)


def load_meta_data() -> dict:
    """
    Loads the meta.json file which contains configuration like served asset directories.
    Returns an empty dict with default structure if the file doesn't exist.
    """
    meta_path = f"{ROOT}/data/meta.json"
    if not os.path.exists(meta_path):
        return {"served_directories": []}
    with open(meta_path, "r") as f:
        return json.load(f)


def save_meta_data(data: dict):
    """
    Saves the meta.json file.
    """
    os.makedirs(f"{ROOT}/data", exist_ok=True)
    meta_path = f"{ROOT}/data/meta.json"
    with open(meta_path, "w") as f:
        json.dump(data, f, indent=2)
