import models
import abc
import itertools
import numpy as np
import scipy.stats
from typing import Any

class Waiter(abc.ABC):
    def __init__(
            self,
            data: list[dict],
            competition_model_match: models.CompetitionModel,
            competition_model_score: models.CompetitionModel,
        ):
        self.competition_model_match = competition_model_match
        self.competition_model_score = competition_model_score
        self.data = data
        self.systems = list(data[0]["scores"].keys())
        self.system_ranking = {sys: [] for sys in self.systems}
        for item in data:
            for sys in self.systems:
                scores = [
                    (score[0]["score"] + score[1]["score"]) / 2
                    for score in item["scores"][sys]
                ]
                self.system_ranking[sys].append(np.mean(scores))
        self.system_ranking = {
            sys: np.mean(ranks) for sys, ranks in self.system_ranking.items()
        }

    @abc.abstractmethod
    def next_match(self):
        pass

    def evaluate_collected(self):
        system_ranking = [self.system_ranking[sys] for sys in self.systems]
        system_ranking_pred = [
            self.competition_model_score.system_score(sys)
            for sys in self.systems
        ]
        return scipy.stats.kendalltau(system_ranking, system_ranking_pred, variant="b").correlation
    

    def record_result(self, sys1: str, sys2: str, result: models.Result):
        self.competition_model_match.record_result(sys1, sys2, result)
        self.competition_model_score.record_result(sys1, sys2, result)


class WaiterBasic(Waiter):
    """
    Always select the match with the highest desireability.
    """

    def __init__(
            self,
            data: list[dict],
            competition_model_match: models.CompetitionModel,
            competition_model_score: models.CompetitionModel,
        ):
        super().__init__(data, competition_model_match, competition_model_score)
        self.system_progress = {
            tuple(sorted(pair)): 0
            for pair in itertools.combinations(self.systems, 2)
        }

    def next_match(self) -> tuple[tuple[str, str, Any], float] | None:
        """
        Return the next match (and the score) or None if no match can take place.
        """
        matches = sorted(
            self.system_progress,
            key=lambda pair: self.competition_model_match.mach_desireability(pair[0], pair[1]),
            reverse=True,
        )
        for sys1, sys2 in matches:
            item = self.data[self.system_progress[(sys1, sys2)]]
            self.system_progress[(sys1, sys2)] += 1

            if self.system_progress[(sys1, sys2)] == len(self.data):
                # we can't sample this pair anymore
                self.system_progress.pop(sys1, sys2)

            human_diff = []
            for score1, score2 in zip(item["scores"][sys1], item["scores"][sys2]):
                score1 = (score1[0]["score"] + score1[1]["score"]) / 2
                score2 = (score2[0]["score"] + score2[1]["score"]) / 2
                if score1 > score2 + 20:
                    human_diff.append(1)
                elif score2 > score1 + 20:
                    human_diff.append(0)
                else:
                    human_diff.append(0.5)

            return (
                (sys1, sys2, item),
                np.mean(human_diff),
            )            

        return None