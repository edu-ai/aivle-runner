import json
import numpy as np
import random

'''
agent
	__init__.py
		def create_agent()
	...
test_suite
	__init__.py
		test_suite = TestSuite()
'''

class TestSuiteNotFound(Exception): pass
class AgentNotFound(Exception): pass

def main():
	try:
		from test_suite import test_suite
	except ModuleNotFoundError as e:
		raise TestSuiteNotFound(str(e))
	try:
		from agent import create_agent
	except ModuleNotFoundError as e:
		raise AgentNotFound(str(e))

	output = test_suite.run(create_agent)

	print(test_suite.json_output)

if __name__ == "__main__":
	main()