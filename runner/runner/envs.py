class TestEnv(object):
	def __init__(self, *args, **kwargs):
		pass

	def run(self, agent):
		raise NotImplemented

	def terminated(self, e):
		raise NotImplemented


class BaseTestEnv(TestEnv):
	def __init__(self, *args, **kwargs):
		self.env = kwargs.get('env')
		self.evaluator = kwargs.get('evaluator')

	def terminated(self, e):
		return self.evaluator.terminated(e)


class SupervisedLearningTestEnv(BaseTestEnv):
	def run(self, agent, *args, **kwargs):
		self.env.reset()
		self.evaluator.reset()
		while True:
			data = self.env.pop()
			if not data:
				break
			x, y = data
			self.evaluator.step(y_true=y, y=agent.step(x), x=x)
		self.evaluator.done()
		return self.evaluator.result


class ReinforcementLearningTestEnv(BaseTestEnv):
	def run(self, agent, *args, **kwargs):
		runs = kwargs.get('runs', 1)
		state = self.env.reset()
		self.evaluator.reset()
		while True:
			if runs <= 0:
				break

			action = agent.step(state)
			next_state, reward, done, info = self.env.step(action)

			full_state = {
				'state': state, 'action': action, 'reward': reward, 
				'next_state': next_state, 'done': done, 'info': info, 'runs': runs
			}
			agent.update(**full_state)
			self.evaluator.step(**full_state)

			if done:
				runs -= 1
				self.env.reset()
		self.evaluator.done()
		return self.evaluator.result