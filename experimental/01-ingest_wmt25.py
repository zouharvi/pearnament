# %%

import json
import collections

with open("../../wmt25-general-mt/data/wmt25-genmt-humeval.jsonl", "r") as f:
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
    data_out[lang].append({
        "doc_id": doc_id,
        "src_text": [seg["src_text"] for _, seg in segments],
        "tgt_text": {
            sys: [seg["tgt_text"][sys] for _, seg in segments]
            for sys in segments[0][1]["tgt_text"].keys()
        },
        "scores": {
            sys: [
                seg["scores"][sys]
                for _, seg in segments
            ]
            for sys in segments[0][1]["scores"].keys()
        },
    })

with open("../server/data/wmt25-genmt-batches.json", "w") as f:
    json.dump([
        {
            "campaign": lang,
            "data": data,
        }
        for lang, data in data_out.items()
    ], f, ensure_ascii=False)
