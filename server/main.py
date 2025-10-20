from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import random
import collections
import json
import model
import difflib
import os
os.makedirs("data", exist_ok=True)


def highlight_differences(a, b):
    """
    Compares two strings and wraps their differences in HTML span tags.

    Args:
        a: The first string.
        b: The second string.

    Returns:
        A tuple containing the two strings with their differences highlighted.
    """
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


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

with open("data/wmt25-genmt-bare.jsonl", "r") as f:
    data = [json.loads(line) for line in f.readlines()]
    systems = list(data[0]["tgt_text"].keys())

# just keep stored how much we evaluated
segment_registry = collections.defaultdict(lambda: -1)
competition_model = model.CompetitionModelELO(systems)

class UIDRequest(BaseModel):
    uid: str

@app.post("/get-next")
async def get_next(request: UIDRequest):
    print(request.uid)
    global segment_registry

    sys1, sys2 = random.sample(systems, 2)
    segment_registry[(sys1, sys2)] += 1
    # TODO: handle overflow better
    if segment_registry[(sys1, sys2)] >= len(data):
        segment_registry[(sys1, sys2)] = 0

    line = data[segment_registry[(sys1, sys2)]]

    texts = [highlight_differences(a, b) for a, b in zip(
        line["tgt_text"][sys1].split("\n\n"),
        line["tgt_text"][sys2].split("\n\n"),
    )]
    
    return JSONResponse(content={
        "doc_id": line["doc_id"],
        # TODO: this is not good sentence splitting
        "src": [line.replace(". ", ".<br><br>") for line in line["src_text"].split("\n\n")],
        "sys_a": sys1,
        "out_a": [line_a.replace(". ", ".<br><br>") for line_a, line_b in texts],
        "sys_b": sys2,
        "out_b": [line_b.replace(". ", ".<br><br>") for line_a, line_b in texts],
    })


async def log_message(message: str):
    with open("data/log.jsonl", "a") as log_file:
        log_file.write(message + "\n")