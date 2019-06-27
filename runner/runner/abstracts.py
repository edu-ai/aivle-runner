# Test Creator

from gym import Env as GymEnv

class Env(GymEnv):
    pass

class Generator(object):
    def __init__(self, *args, **kwargs):
        pass

    def reset(self):
        raise NotImplemented

    def pop(self):
        raise NotImplemented

class EvaluationResult(object):
    def __init__(self, *args, **kwargs):
        pass

    def __str__(self):
        raise NotImplemented

    def __int__(self):
        raise NotImplemented

    @property
    def json(self):
        raise NotImplemented

class Evaluator(object):
    def __init__(self, *args, **kwargs):
        pass

    def reset(self, *args, **kwargs):
        raise NotImplemented

    def step(self, *args, **kwargs):
        raise NotImplemented

    def done(self, *args, **kwargs):
        raise NotImplemented

    def terminated(self, e):
        return

    @property
    def result(self):
        return EvaluationResult()

def compute_point(results):
    raise NotImplemented


# Test Taker

class Agent(object):
    def __init__(self, *args, **kwargs):
        pass

    def step(self, state, *args, **kwargs):
        raise NotImplemented

    def update(self, *args, **kwargs):
        return

def create_agent(test_case_id, *args, **kwargs):
    raise NotImplemented