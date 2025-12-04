import json
import os

ROOT = "."

# Sentinel value to indicate a task reset - masks all prior annotations
RESET_MARKER = "__RESET__"


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
    Can be empty. Respects reset markers - if a reset marker is found,
    only entries after the last reset are returned.
    """
    log = get_db_log(campaign_id)
    
    # Filter matching entries
    matching = [
        entry for entry in log
        if (
            (user_id is None or entry.get("user_id") == user_id) and
            (item_i is None or entry.get("item_i") == item_i)
        )
    ]
    
    # Find the last reset marker for this user (if any)
    last_reset_idx = -1
    for i, entry in enumerate(matching):
        if entry.get("annotations") == RESET_MARKER:
            last_reset_idx = i
    
    # Return only entries after the last reset
    if last_reset_idx >= 0:
        matching = matching[last_reset_idx + 1:]
    
    return matching


def save_db_payload(campaign_id: str, payload: dict):
    """
    Saves the given payload to the log for the given campaign_id, user_id and item_i.
    Saves both on disk and in-memory.
    """
    # Ensure the in-memory cache is initialized before writing to file
    # to avoid reading back the same entry we're about to append
    log = get_db_log(campaign_id)

    log_path = f"{ROOT}/data/outputs/{campaign_id}.jsonl"
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, "a") as log_file:
        log_file.write(json.dumps(payload, ensure_ascii=False,) + "\n")

    log.append(payload)
