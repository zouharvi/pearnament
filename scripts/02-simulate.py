# %%

import json
import models
import waiters

with open("../server/data/wmt25-genmt-batches.json", "r") as f:
    data = json.load(f)[0]["data"]

# %%
waiter = waiters.WaiterBasic(
    data,
    competition_model_match=models.CompetitionModelRandomUniform(list(data[0]["scores"].keys())),
    competition_model_score=models.CompetitionModelELO(list(data[0]["scores"].keys())),
)

for i in range(1, 10_000+1):
    ((sys1, sys2, item), result) = waiter.next_match()
    waiter.record_result(sys1, sys2, result)
    # print(f"Match: {sys1:>15} vs {sys2:<15} => winner: {result:.0%}")
    if i % 500 == 0:
        print(i, waiter.evaluate_collected())

# %%

len(list(data[0]["scores"].keys()))