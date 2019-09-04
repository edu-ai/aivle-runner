import os
import json
import logging
import settings
import utils


logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel("DEBUG")

if settings.Runner.USE_DOCKER:
	import docker
	client = docker.from_env()
else:
	import virtualenv
	client = virtualenv.Client()

print('Using:', client)

class RunnerType:
	Docker = 'DO'
	Python = 'PY'


class ImageNotFound(Exception):
	pass

class UnexpectedRunnerType(Exception):
	pass

class RunnerInstallError(Exception):
	pass

class AgentInstallError(Exception):
	pass

class SuiteInstallError(Exception):
	pass

class RunnerError(Exception):
	pass

class MaxImageSizeExceeded(Exception):
	pass

class MalformedOutputError(Exception):
	pass


class Runnable(object):
	def __init__(self, ts_id, agent_id, runner_type=RunnerType.Python, 
		pull_time_limit=settings.Runner.PULL_TIME_LIMIT, setup_time_limit=settings.Runner.SETUP_TIME_LIMIT, 
		run_time_limit=settings.Runner.RUN_TIME_LIMIT, max_image_size=settings.Runner.MAX_IMAGE_SIZE, 
		image=None, rand_len=32, **kwargs):
		self.ts_id = ts_id
		self.agent_id = agent_id
		self.runner_type = runner_type
		self.metadata = kwargs.get('metadata', None)
		self.rand = utils.generate_secure_string(rand_len)
		self.set_image(self.runner_type, image)
		self.devices = []
		self.container = None
		self.pull_time_limit = pull_time_limit
		self.setup_time_limit = setup_time_limit
		self.run_time_limit = run_time_limit
		self.max_image_size = max_image_size

	@property
	def container_name(self):
		return "aiVLE-runner-TS.{}-A.{}-{}".format(self.ts_id, self.agent_id, self.rand)

	@property
	def output_path(self):
		return os.path.join(settings.OUTPUT_PATH, str(self.ts_id), "{}.json".format(self.agent_id))

	def log(self, message, log_type='info'):
		getattr(logger, log_type)("[TS={}, A={}, R={}, M={}] {}".format(self.ts_id, self.agent_id, self.runner_type, self.metadata, message))


	def set_image(self, runner_type, image=None):
		if self.runner_type == RunnerType.Python:
			self.image = settings.Runner.PYTHON_DOCKER_IMAGE
		elif self.runner_type == RunnerType.Docker:
			if not image:
				raise ImageNotFound
			self.image = image
		else:
			raise UnexpectedRunnerType

	def path_in_host(self, name):
		if name == 'agent': return os.path.join(settings.AGENTS_PATH, "{}.zip".format(self.agent_id))
		elif name == 'suite': return os.path.join(settings.SUITES_PATH, "{}.zip".format(self.ts_id))
		else: raise NotImplemented

	def path_in_container(self, name):
		if name in ['agent', 'suite']: name = "{}.zip".format(name)
		return os.path.join('/', self.container_name, name)

	def pull_image(self):
		self.log('Pulling image: {}'.format(self.image))
		client.images.pull(self.image)

	def run_container(self):
		self.log('Running container image: {}'.format(self.image))
		self.volumes = {
			settings.RUNNER_PATH: {'bind': self.path_in_container('runner'), 'mode': 'ro'},
			self.path_in_host('agent'): {'bind': self.path_in_container('agent'), 'mode': 'ro'},
			self.path_in_host('suite'): {'bind': self.path_in_container('suite'), 'mode': 'ro'},
		}
		self.container = client.containers.create(self.image, volumes=self.volumes, stdin_open=True, name=self.container_name)
		self.container.start()

	def exec_run(self, command, exception=None, **kwargs):
		self.log('Running command: {}'.format(command))
		exit_code, output = self.container.exec_run(command, **kwargs)
		output = output.decode('utf8')
		if exit_code > 0 and exception:
			raise exception(output)
		self.log('\n{}'.format(output))
		return exit_code, output

	def pip_install(self, items, r=False, exception=None, **kwargs):
		return self.exec_run("pip install{} {}".format(' -r' if r else '', items), exception, **kwargs)

	def connect(self, network_name='bridge'):
		client.networks.list(names=[network_name])[0].connect(self.container)
		self.log('Connected to: {}'.format(network_name))

	def disconnect(self, network_name='bridge'):
		client.networks.list(names=[network_name])[0].disconnect(self.container)
		self.log('Disconnected from: {}'.format(network_name))

	def run(self):
		self.log('Running container: TS.{}, A.{}, RT.{}, RTL.{}'.format(self.ts_id, self.agent_id, self.runner_type, self.run_time_limit))
		output = (None, None) # (error, data)
		try:
			with utils.time_limit(self.pull_time_limit, 'Image pull time limit exceeded'):
				self.pull_image()
				if client.images.get(self.image).attrs['Size']/1000 > self.max_image_size:
					raise MaxImageSizeExceeded()

				if not self.container:
					self.run_container()

			with utils.time_limit(self.setup_time_limit, 'Setup time limit exceeded'):
				# Install
				self.pip_install(self.path_in_container('runner'), exception=RunnerInstallError)
				if self.runner_type == RunnerType.Python:
					self.disconnect()
					self.pip_install(self.path_in_container('agent'), exception=AgentInstallError)
					self.connect()
				self.pip_install(self.path_in_container('suite'), exception=SuiteInstallError)

			with utils.time_limit(self.run_time_limit, 'Run time limit exceeded'):
				# Execute runner
				exit_code, output = self.exec_run("runner", exception=RunnerError)
				try:
					data = json.loads(output)
				except json.JSONDecodeError as e:
					raise MalformedOutputError(str(e), output)

				# Save output for the future
				os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
				with open(self.output_path, 'w') as outfile:
					json.dump(data, outfile)

				output = (None, data)
		except Exception as e:
			template = "An exception of type {0} occurred. Arguments: {1!r}"
			message = template.format(type(e).__name__, e.args)
			self.log(message, log_type='error')
			output = (e, None)
		finally:
			self.destroy()
			return output

	def destroy(self):
		self.log('Destroying container image: {}'.format(self.image))
		if self.container:
			self.container.kill()
			self.container.remove()
		if self.runner_type == RunnerType.Docker:
			try:
				client.images.get(self.image) # check image exists
				client.images.delete(self.image)
			except docker.errors.ImageNotFound:
				pass