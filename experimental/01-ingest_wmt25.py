import os
import json
import collections
import random
os.chdir(os.path.dirname(os.path.abspath(__file__)) + "/../")

with open("../wmt25-general-mt/data/wmt25-genmt-humeval.jsonl", "r") as f:
    data_wmt = [json.loads(line) for line in f.readlines()]

documents = collections.defaultdict(list)

for line in data_wmt:
    doc_id, seg_id = line["doc_id"].rsplit("_#_", 1)
    documents[doc_id].append((seg_id, line))

data_out = collections.defaultdict(list)
for doc_id, segments in documents.items():
    if "_#_speech_#_" in doc_id or "_#_social_#_" in doc_id or "_#_literary_#_" in doc_id:
        continue
    lang = doc_id.split("_#_")[0]
    segments.sort(key=lambda x: x[0])
    for sys in segments[0][1]["tgt_text"].keys():
        data_out[lang].append({
            "doc_id": doc_id,
            "sys_id": sys,
            "src": [seg["src_text"] for _, seg in segments],
            # hotfix
            "tgt": [seg["tgt_text"][sys].replace("< / i>", "</i>") for _, seg in segments],
        })

r = random.Random(0)

for lang, data in data_out.items():
    # chunk to 40 documents per task
    data_new = []
    r.shuffle(data)
    for i in range(0, len(data), 40):
        chunk = data[i:i + 10]
        data_new.append(chunk)
    
    with open(f"server/examples/wmt25_#_{lang}.json", "w") as f:
        lang1, lang2 = lang.split("-")
        json.dump(
            {
                "info": {
                    "type": "task-based",
                    "template": "pointwise",
                    "protocol": "ESA",
                    "status_message": f"Evaluate translation from {lang1} to {lang2}",
                    "server_url": "http://localhost:8001",
                    "frontend_url": "http://localhost:8000",
                },
                "campaign_id": f"wmt25_#_{lang}",
                # just first 5 users to keep the size small
                "data": data_new[:5],
            },
            f,
            ensure_ascii=False,
            indent=2
        )
