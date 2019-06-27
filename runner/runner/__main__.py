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

def main():
	from test_suite import test_suite
	from agent import create_agent

	output = test_suite.run(create_agent)

	print(test_suite.json_output)

if __name__ == "__main__":
	main()