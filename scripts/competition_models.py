import abc
import random
import numpy as np
import itertools

Result = float

class CompetitionModel(abc.ABC):
    @abc.abstractmethod
    def __init__(self, systems: list[str]):
        pass

    @abc.abstractmethod
    def mach_desireability(self, sys1: str, sys2: str) -> float:
        pass

    @abc.abstractmethod
    def record_result(self, sys1: str, sys2: str, result: Result):
        pass

    @abc.abstractmethod
    def system_score(self, sys: str) -> float:
        pass


class CompetitionModelTrueSkill(CompetitionModel):
    def __init__(self, systems: list[str]):
        # TODO: load
        pass

    def system_score(self, sys: str) -> float:
        pass

    def mach_desireability(self, sys1: str, sys2: str):
        pass

    def record_result(self, sys1: str, sys2: str, result: Result):
        assert result >= 0 and result <= 1
        pass


class CompetitionModelELO(CompetitionModel):
    def __init__(self, systems: list[str]):
        self.scores = {sys: [] for sys in systems}

    def system_score(self, sys: str) -> float:
        out = 1000
        for opponent, result in self.scores[sys]:
            out += opponent + result
        return out/len(self.scores[sys]) if self.scores[sys] else out

    def mach_desireability(self, sys1: str, sys2: str):
        raise NotImplementedError()

    def record_result(self, sys1: str, sys2: str, result: Result):
        assert result >= 0 and result <= 1
        self.scores[sys1].append((self.system_score(sys2), 1600*result - 800))
        self.scores[sys2].append(
            (self.system_score(sys1), 1600*(1-result) - 800))


class CompetitionModelRandom(CompetitionModel):
    """
    Fully randomly select a match.
    """

    def __init__(self, systems: list[str]):
        self.scores = {sys: [] for sys in systems}
        self.random = random.Random(hash(tuple(systems)))

    def system_score(self, sys: str) -> float:
        """
        Simple proportion of wins (or partial wins).
        """

        if not self.scores[sys]:
            return np.mean(0.5)
        else:
            return np.mean(self.scores[sys])

    def mach_desireability(self, sys1: str, sys2: str):
        return self.random.random()

    def record_result(self, sys1: str, sys2: str, result: Result):
        assert result >= 0 and result <= 1
        self.scores[sys1].append(result)
        self.scores[sys2].append(1-result)



class CompetitionModelRandomUniform(CompetitionModelRandom):
    """
    Randomly select a match that's balanced between all systems.
    """

    def __init__(self, systems: list[str]):
        super().__init__(systems)
        self.queue = itertools.cycle((tuple(sorted(pair)) for pair in itertools.combinations(systems, 2)))
        self.next = next(self.queue)
        
    def mach_desireability(self, sys1: str, sys2: str):
        if (sys1, sys2) == self.next:
            return 1.0
        else:
            return 0.0
    
    def record_result(self, sys1: str, sys2: str, result: Result):
        super().record_result(sys1, sys2, result)
        assert self.next == (sys1, sys2)
        self.next = next(self.queue)