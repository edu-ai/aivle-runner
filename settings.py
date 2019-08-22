import os
from dotenv import load_dotenv
load_dotenv()

BASE_PATH = os.path.dirname(os.path.realpath(__file__))
RUNNER_PATH = os.path.join(BASE_PATH, 'runner-kit')
AGENTS_PATH = os.path.join(BASE_PATH, 'agents')
SUITES_PATH = os.path.join(BASE_PATH, 'suites')
OUTPUT_PATH = os.path.join(BASE_PATH, 'outputs')

class Runner:
    PYTHON_DOCKER_IMAGE = 'python:3.7'
    PULL_TIME_LIMIT = 10 * 60 # seconds
    SETUP_TIME_LIMIT = 10 * 60 # seconds
    RUN_TIME_LIMIT = 1 * 60 * 60 # seconds
    MAX_IMAGE_SIZE = 1000000 # KB
    USE_DOCKER = False

class VirtualEnv:
    PYTHON_VERSION = '3.7.2'
    ROOT_PATH = os.getenv("VIRTUALENV_ROOT") or os.path.join(BASE_PATH, 'virtualenvs')
    USE_FIREJAIL = True

class Watcher:
    API = os.getenv("WATCHER_API")
    USERNAME = os.getenv("WATCHER_USERNAME")
    PASSWORD = os.getenv("WATCHER_PASSWORD")
    SLEEP = 5
    PROCESSES = 1