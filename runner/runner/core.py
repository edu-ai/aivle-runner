from .utils import time
from collections import namedtuple
from enum import Enum
import json


TestCaseResult = namedtuple('TestCaseResult', ['test_case', 'evaluation', 'error'])
TestSuiteResult = namedtuple('TestSuiteResult', ['test_suite', 'results', 'point'])


class TestCase(object):
	def __init__(self, identifier, test_env, time_limit=None, **kwargs):
		self.identifier = identifier
		self.test_env = test_env
		self.time_limit = time_limit
		self.runs = kwargs.get('runs', 1)

	def run(self, agent):
		error = None
		evaluation = None
		try:
			with time.time_limit(self.time_limit):
				evaluation = self.test_env.run(agent, runs=self.runs)
		except Exception as e: # also catch TimeoutException
			error = e
			evaluation = self.test_env.terminated(e)
		finally:
			return TestCaseResult(self, evaluation, error)


class TestSuite(object):
	def __init__(self, identifier, test_cases, point_fn=None):
		self.identifier = identifier
		self.test_cases = test_cases
		self.point_fn = point_fn

	def run(self, agent_create_fn):
		self.results = []
		self.point = None
		for tc in self.test_cases:
			agent = agent_create_fn(tc.identifier)
			result = tc.run(agent)
			self.results.append(result)
		if self.point_fn:
			self.point = self.point_fn(self.results)
		return TestSuiteResult(self, self.results, self.point)

	@property
	def json_output(self):
		test_cases = {}
		for res in self.results:
			test_cases[res.test_case.identifier] = res.evaluation.json
		data = {
			'identifier': self.identifier,
			'test_cases': test_cases,
			'point': self.point
		}
		return json.dumps(data)