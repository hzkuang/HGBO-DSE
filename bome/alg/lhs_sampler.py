from typing import Any
from typing import Dict
from typing import Optional

import numpy

from optuna import distributions
from optuna.distributions import BaseDistribution
from optuna.samplers import BaseSampler
from optuna.study import Study
from optuna.trial import FrozenTrial


class LatinHypercubeSampler(BaseSampler):

    def __init__(self, init_params=None, seed: Optional[int] = None) -> None:
        self._rng = numpy.random.RandomState(seed)
        self._init_params = init_params

    def reseed_rng(self) -> None:
        self._rng.seed()

    def infer_relative_search_space(
        self, study: Study, trial: FrozenTrial
    ) -> Dict[str, BaseDistribution]:
        return {}

    def sample_relative(
        self, study: Study, trial: FrozenTrial, search_space: Dict[str, BaseDistribution]
    ) -> Dict[str, Any]:
        return {}

    def sample_independent(
        self,
        study: Study,
        trial: FrozenTrial,
        param_name: str,
        param_distribution: distributions.BaseDistribution,
    ) -> Any:
        # search_space = {param_name: param_distribution}
        idx = trial.number
        param_value = self._init_params[param_name][idx]

        return param_value
