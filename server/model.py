# ruff: noqa

raise Exception("Deprecated")
"""
See scripts/models.py for a list of possible competition models.
"""

import json
import os
import random

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

class CompetitionModel():
    def __init__(self, systems):
        if os.path.exists("data/model_elo.json"):
            with open("data/model_elo.json", "r") as f:
                self.scores = json.load(f)
        else:
            print("Initializing new ELO model")
            self.scores = {sys: [] for sys in systems}

    def system_score(self, sys):
        out = 1000
        for opponent, result in self.scores[sys]:
            out += opponent + result
        return out/len(self.scores[sys]) if self.scores[sys] else out

    def future_information(self, sys1, sys2):
        pass

    def record_result(self, sys1, sys2, result):
        self.scores[sys1].append((self.system_score(sys2), 1600*result - 800))
        self.scores[sys2].append((self.system_score(sys1), 1600*(1-result) - 800))

        self.save()

    def save(self):
        with open("data/model_elo.json", "w") as f:
            json.dump(self.scores, f)