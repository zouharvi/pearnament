from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import random
import collections
import json
from .model import CompetitionModel
from .utils import highlight_differences
import os
os.makedirs("data", exist_ok=True)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

with open("data/wmt25-genmt-batches.json", "r") as f:
    data = json.load(f)[0]["data"]
    systems = list(data[0]["tgt_text"].keys())

# just keep stored how much we evaluated
segment_registry = collections.defaultdict(lambda: -1)
competition_model = CompetitionModel(systems)

@app.post("/get-next")
async def get_next(uid: str):
    print(uid)
    global segment_registry

    sys1, sys2 = random.sample(systems, 2)
    segment_registry[(sys1, sys2)] += 1
    # TODO: handle overflow better
    if segment_registry[(sys1, sys2)] >= len(data):
        segment_registry[(sys1, sys2)] = 0

    line = data[segment_registry[(sys1, sys2)]]

    texts = [highlight_differences(a, b) for a, b in zip(
        line["tgt_text"][sys1],
        line["tgt_text"][sys2],
    )]
    
    return JSONResponse(content={
        "doc_id": line["doc_id"],
        # TODO: this is not good sentence splitting
        "src": [line.replace(". ", ".<br><br>") for line in line["src_text"]],
        "sys_a": sys1,
        "out_a": [line_a.replace(". ", ".<br><br>") for line_a, line_b in texts],
        "sys_b": sys2,
        "out_b": [line_b.replace(". ", ".<br><br>") for line_a, line_b in texts],
    })


async def log_message(message: str):
    # TODO: log into some common directory
    with open("data/log.jsonl", "a") as log_file:
        log_file.write(message + "\n")