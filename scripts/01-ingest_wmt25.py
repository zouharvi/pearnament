# %%

import json
import collections

with open("../../wmt25-general-mt/data/wmt25-genmt-humeval.jsonl", "r") as f:
    data_wmt = [json.loads(line) for line in f.readlines()]

documents = collections.defaultdict(list)

for line in data_wmt:
    line.pop("scores")
    doc_id, seg_id = line["doc_id"].rsplit("_#_", 1)
    documents[doc_id].append((seg_id, line))

with open("../server/data/wmt25-genmt-bare.jsonl", "w") as f:
    for doc_id, segments in documents.items():
        if "_#_speech_#_" in doc_id or "_#_social_#_" in doc_id:
            continue
        segments.sort(key=lambda x: x[0])

        f.write(json.dumps({
            "doc_id": doc_id,
            "src_text": "\n\n".join(seg["src_text"] for _, seg in segments),
            "tgt_text": {
                sys: "\n\n".join(
                    seg["tgt_text"][sys] for _, seg in segments
                )
                for sys in segments[0][1]["tgt_text"].keys()
            }
        }, ensure_ascii=False) + "\n")