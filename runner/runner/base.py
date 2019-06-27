from .abstracts import EvaluationResult, Evaluator

DEFAULT_ERROR_VALUE = 0

class BaseEvaluationResult(EvaluationResult):
    def __init__(self, *args, **kwargs):
        self.name = kwargs.get('name', 'score')
        self.value = kwargs.get('value')
        self.results = kwargs.get('results', [])
        self.error = kwargs.get('error', None)

    def __str__(self):
        if self.error: return self.error
        str_results = " ".join(map(lambda x: str(x), self.results))
        return str_results

    def __int__(self):
        if self.error: return DEFAULT_ERROR_VALUE
        return self.value

    @property
    def json(self):
        return {
            self.name: self.__int__(),
            'details': self.__str__()
        }

class SklearnMetricEvaluationResult(BaseEvaluationResult):
    pass

class RewardEvaluationResult(BaseEvaluationResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = 'cumulative rewards'

class BaseEvaluator(Evaluator):
    def __init__(self, *args, **kwargs):
        self.error = None

    def reset(self, *args, **kwargs):
        self.error = None

    def terminated(self, e):
        self.error = e

class SklearnMetricEvaluator(BaseEvaluator):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.metric = kwargs.get('metric')
        self.metric_kwargs = kwargs.get('metric_kwargs', {})
        self.result_class = kwargs.get('result_class', None)
        self.reset()
        
    def reset(self, *args, **kwargs):
        super().reset(*args, **kwargs)
        self.ys_true = []
        self.ys = []

    def step(self, *args, **kwargs):
        self.ys_true.append(kwargs.get('y_true'))
        self.ys.append(kwargs.get('y'))

    def done(self, *args, **kwargs):
        self.value = self.metric(self.ys_true, self.ys, **self.metric_kwargs)

    @property
    def result(self):
        results=(self.ys_true, self.ys)
        if self.result_class:
            return self.result_class(name=self.metric.__name__, value=self.value, results=results, error=self.error)
        return SklearnMetricEvaluationResult(name=self.metric.__name__, value=self.value, results=results, error=self.error)

class RewardEvaluator(BaseEvaluator):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.reset()
        
    def reset(self, *args, **kwargs):
        super().reset(*args, **kwargs)
        self.rewards = []

    def step(self, *args, **kwargs):
        self.rewards.append(kwargs.get('reward'))

    def done(self, *args, **kwargs):
        self.cum_rewards = sum(self.rewards)

    @property
    def result(self):
        return RewardEvaluationResult(value=self.cum_rewards, results=self.rewards, error=self.error)

class ComputePoint:
    def sum_values(results):
        return sum([int(res.evaluation) for res in results])

    def sum_positives(results):
        return sum([int(res.evaluation) for res in results if int(res.evaluation) > 0])

    def count_positives(results):
        return sum([1 for res in results if int(res.evaluation) > 0])