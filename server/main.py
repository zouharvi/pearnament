from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import random
import collections
import json
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

with open("data/wmt25-genmt-bare.jsonl", "r") as f:
    data = [json.loads(line) for line in f.readlines()]
    systems = list(data[0]["tgt_text"].keys())

# just keep stored how much we evaluated
competition_model = collections.defaultdict(lambda: -1)

class UIDRequest(BaseModel):
    uid: str

@app.post("/get-next")
async def get_next(request: UIDRequest):
    print(request.uid)
    global competition_model

    sys1, sys2 = random.sample(systems, 2)
    competition_model[(sys1, sys2)] += 1
    # TODO: handle overflow better
    if competition_model[(sys1, sys2)] >= len(data):
        competition_model[(sys1, sys2)] = 0

    line = data[competition_model[(sys1, sys2)]]

    # TODO: compute highlighting?
    
    return JSONResponse(content={
        "doc_id": line["doc_id"],
        "src": line["src_text"].split("\n\n"),
        "sys_a": sys1,
        "out_a": line["tgt_text"][sys1].split("\n\n"),
        "sys_b": sys2,
        "out_b": line["tgt_text"][sys2].split("\n\n"),
    })


async def log_message(message: str):
    with open("data/log.jsonl", "a") as log_file:
        log_file.write(message + "\n")