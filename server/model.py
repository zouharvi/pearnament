import json
import os


class CompetitionModelTrueSkill():
    def __init__(self):
        # TODO: load
        pass

    def future_information(self, sys1, sys2):
        pass

    def record_result(self, sys1, sys2, result):
        pass

        self.save()

    def save(self):
        pass


class CompetitionModelELO():
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