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