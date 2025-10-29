# %%

import json
import competition_models
import competition_waiters

with open("../server/data/wmt25-genmt-batches.json", "r") as f:
    data = json.load(f)[0]["data"]

# %%
waiter = competition_waiters.CompetitionWaiterBasic(
    data,
    competition_model_match=competition_models.CompetitionModelRandomUniform(list(data[0]["scores"].keys())),
    competition_model_score=competition_models.CompetitionModelELO(list(data[0]["scores"].keys())),
)

for i in range(1, 10_000+1):
    ((sys1, sys2, item), result) = waiter.next_match()
    waiter.record_result(sys1, sys2, result)
    # print(f"Match: {sys1:>15} vs {sys2:<15} => winner: {result:.0%}")
    if i % 500 == 0:
        print(i, waiter.evaluate_collected())

# %%

len(list(data[0]["scores"].keys()))