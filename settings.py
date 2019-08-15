import os

BASE_PATH = os.path.dirname(os.path.realpath(__file__))
RUNNER_PATH = os.path.join(BASE_PATH, 'runner')
AGENTS_PATH = os.path.join(BASE_PATH, 'agents')
SUITES_PATH = os.path.join(BASE_PATH, 'suites')
OUTPUT_PATH = os.path.join(BASE_PATH, 'outputs')

class Runner:
    PYTHON_DOCKER_IMAGE = 'python:3.7'
    PULL_TIME_LIMIT = 5 * 60 # seconds
    SETUP_TIME_LIMIT = 1 * 60 # seconds
    RUN_TIME_LIMIT = 1 * 60 * 60 # seconds
    MAX_IMAGE_SIZE = 1000000 # KB
    USE_DOCKER = False

class VirtualEnv:
    PYTHON_VERSION = '3.7.2'
    ROOT_PATH = os.path.join(BASE_PATH, 'virtualenvs')

class Watcher:
    API = 'http://127.0.0.1:8000/api/v1/jobs/'
    USERNAME = 'rizkiarm'
    PASSWORD = '1'
    SLEEP = 5
    PROCESSES = 1