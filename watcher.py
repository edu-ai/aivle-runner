import requests
import json
import time
import shutil
import os
import logging

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel("DEBUG")

import settings, utils, core

class Status:
    QUEUED = 'Q'
    RUNNING = 'R'
    ERROR = 'E'
    DONE = 'D'

class BaseAPI(object):
    def __init__(self, auth=None):
        self.session = requests.Session()
        self.session.auth = auth
        
    def request(self, url, method='get', **kwargs):
        assert method in ['get', 'post', 'delete', 'put']
        response = getattr(self.session, method)(url, **kwargs)
        return response
        
    def download(self, url, filepath):
        response = self.session.get(url, stream=True)
        with open(filepath, 'wb') as out_file:
            shutil.copyfileobj(response.raw, out_file)
        return response
        
class API(BaseAPI):
    def __init__(self, base_url, auth=None):
        super().__init__(auth=auth)
        self.base_url = base_url
        self.base = super()
        
    def request(self, id=None, action=None, method='get', **kwargs):
        assert method in ['get', 'post', 'delete', 'put']
        url = self.base_url
        if id: url += str(id) + '/'
        if action: url += format(action) + '/'
        return super().request(url, method=method, **kwargs)


class JobRunner(object):
    def __init__(self, job, *args, **kwargs):
        self.job = job
        self.task = None
        self.api = kwargs.get('api')
        self.retry = kwargs.get('retry', 3)
        self.retry_delay = kwargs.get('retry_delay', 10)
        
    def run_job(self):
        response = self.api.request(id=self.job['id'], action='run', method='post')
        if response.status_code != 200:
            raise Exception('Job run failed')
        
    def get_task(self):
        response = self.api.base.request(self.job['task'])
        if response.status_code != 200:
            raise Exception('Task download failed')
        self.task = response.json()
    
    def path(self, name, id):
        assert name in ['agent', 'suite']
        if not self.task: raise Exception('Task is not initialized')
        base_path = settings.AGENTS_PATH if name == 'agent' else settings.SUITES_PATH
        return os.path.join(base_path, "{}.zip".format(id))
    
    @property
    def agent_path(self):
        return self.path('agent', self.job['id'])
    
    @property
    def suite_path(self):
        return self.path('suite', self.task['id'])
    
    def maybe_download_suite(self):
        if not os.path.isfile(self.suite_path):
            logger.info('Suite not found, downloading...')
            response = self.api.download(self.task['file_url'], self.suite_path)
            if response.status_code != 200:
                raise Exception('Suite download failed')

        with open(self.suite_path, 'rb') as f:
            file_hash = utils.hash_file(f)
            if file_hash != self.task['file_hash']:
                logger.info('Suite hash mismatch ({} != {}), updating...'.format(file_hash, self.task['file_hash']))
                response = self.api.download(self.task['file_url'], self.suite_path)
                if response.status_code != 200:
                    raise Exception('Suite download failed')
                    
    def maybe_download_agent(self):
        if self.job['runner'] == core.RunnerType.Python:
            logger.info('Python runner, downloading agent...')
            response = self.api.download(self.job['file_url'], self.agent_path)
            if response.status_code != 200:
                raise Exception('Agent download failed')
                
    def runnable_run(self):
        runnable = core.Runnable(self.task['id'], self.job['id'])
        return runnable.run()
    
    def process(self, output):
        error, result = output
        notes = json.dumps({'error': {'message':str(error)}} if error else result['test_cases'])
        data = {
            'status': Status.DONE if not error else Status.ERROR,
            'point': None if error else result['point'],
            'notes': notes,
        }
        logger.info('Process done:\n{}'.format(data))
        return data

    def end(self, data):
        try:
            response = self.api.request(id=self.job['id'], action='end', method='post', json=data)
            output = (response.status_code, response.text)
        except:
            output = (-1, None)
        if output[0] != 200:
            logger.error('End failed: {}'.format(output))
            if self.retry > 0:
                time.sleep(self.retry_delay)
                logger.info('Retrying... [{}]'.format(self.retry))
                self.retry -= 1
                self.end(data)
            else:
                logger.info('Max retry reached')
    
    def run(self):
        try:
            self.get_task()
            self.run_job()
            self.maybe_download_suite()
            self.maybe_download_agent()
            output = self.runnable_run()
        except Exception as e:
            logger.error(e)
            output = (e, None)
        finally:
            data = self.process(output)
            self.end(data)

            
class Watcher(object):
    def __init__(self, api, sleep=settings.Watcher.SLEEP, **kwargs):
        self.api = api
        self.sleep = sleep
        
    def watch(self):
        more = False
        while True:
            if not more:
                time.sleep(self.sleep)
            try:
                r = self.api.request()
                if r.status_code != 200:
                    more = False
                    continue
                more = self.handler(r.json())
            except:
                more = False
            
    def handler(self, data):
        raise NotImplemented
            
class JobWatcher(Watcher):
    def __init__(self, *args, **kwargs):
        self.processes = kwargs.pop('processes', settings.Watcher.PROCESSES)
        super().__init__(*args, **kwargs)
        
    def handler(self, data):
        if len(data) == 0:
            return False
        for job in data[:self.processes]:
            job_runner = JobRunner(job, api=self.api)
            job_runner.run()
        return len(data) - len(data[:self.processes]) > 0

    
api = API(settings.Watcher.API, (settings.Watcher.USERNAME, settings.Watcher.PASSWORD))
watcher = JobWatcher(api, sleep=settings.Watcher.SLEEP, processes=settings.Watcher.PROCESSES)
watcher.watch()