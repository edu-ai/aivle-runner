import settings

import shutil
import os
import requests
import logging
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel("DEBUG")


class BaseAPI(object):
    def __init__(self, auth=None, verify=False):
        self.session = requests.Session()
        self.session.auth = auth
        self.verify = verify
        
    def request(self, url, method='get', **kwargs):
        assert method in ['get', 'post', 'delete', 'put']
        response = getattr(self.session, method)(url, verify=self.verify, **kwargs)
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

# ---

api = API(settings.Submission.API, (settings.Watcher.USERNAME, settings.Watcher.PASSWORD))

def agent_path(submission_id):
    return os.path.join(settings.AGENTS_PATH, "{}.zip".format(submission_id))

def maybe_download_agent(submission):
    path = agent_path(submission['id'])
    if not os.path.isfile(path):
        logger.info('Agent not found, downloading...')
        print(submission['file_url'], path)
        response = api.download(submission['file_url'], path)
        if response.status_code != 200:
            raise Exception('Agent download failed', response.status_code)
        return
    logger.info('Agent already exists, skipped.')

next_url = settings.Submission.API
while next_url is not None:
    print(next_url)
    response = api.base.request(next_url)
    if response.status_code != 200:
        raise Exception('Traversal failed:', next_url, response.status_code)
    submissions = response.json()
    next_url = submissions['next']
    for submission in submissions['results']:
        # print(submission)
        maybe_download_agent(submission)
