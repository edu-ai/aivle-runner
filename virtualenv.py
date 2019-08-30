import utils
import settings
import os
import subprocess
import re
import shutil
from distutils.dir_util import copy_tree
from distutils.file_util import copy_file


if settings.VirtualEnv.USE_FIREJAIL:
    ROOT_PATH = os.path.join(os.environ.get('XDG_RUNTIME_DIR'), os.environ.get('USER'))
    SHARED_PATH = os.path.join(ROOT_PATH, 'shared')
else:
    ROOT_PATH = settings.VirtualEnv.ROOT_PATH


def exec(command):
    print('Executing:', command)
    p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    out, err = p.communicate()
    exit_code = p.returncode

    output = out
    if err:
        output = err

    print(exit_code, output)
    return exit_code, output
    
  

class Network(object):
    def connect(self, container):
        container.network = True

    def disconnect(self, container):
        container.network = False


class Networks(object): 
    def list(self, names=[]):
        return [Network()]


class Image(object):
    def __init__(self):
        self.attrs = {}
        self.attrs['Size'] = 0


class Images(object):
    def pull(self, name):
        pass

    def get(self, name):
        return Image()

    def delete(self, name):
        pass


class Container(object): # WARNING: no support for multiple instance existing at the same time
    def __init__(self, image, **kwargs):
        self.image = image
        self.volumes = kwargs.get('volumes', {})
        self.name = kwargs.get('name', utils.generate_secure_string(16))
        self.path = os.path.join(ROOT_PATH, self.name)
        self.network = True

    def get_path(self, path):
        return os.path.join(self.path, *path.split('/'))
          
    def replace_abspath(self, command):
        matches = re.finditer(r" (\/[a-zA-Z.-_]*)", command, re.MULTILINE)

        for match in matches:
            path = match.groups()[0]
            relative_path = self.get_path(path)
            command = command.replace(path, relative_path)

        return command

    def start(self):
        # Create working folder and cd
        os.makedirs(self.path, exist_ok=True)
        os.chdir(self.path)
        # Provide pyenv for firejail
        if settings.VirtualEnv.USE_FIREJAIL:
            self._exec_run('curl https://pyenv.run | bash')
            self._exec_run('pyenv install {}'.format(self.image))
        # Create virtual environment
        self._exec_run('pyenv virtualenv {} {}'.format(self.image, self.name))
        # Update pip
        self.exec_run('pip install --upgrade pip')
        # Symlink volumes to working folder
        for src, dst in self.volumes.items():
            relative_dst = self.get_path(dst['bind'])
            os.makedirs(os.path.dirname(relative_dst), exist_ok=True)
            try:
                os.remove(relative_dst)
            except:
                pass
            if settings.VirtualEnv.USE_FIREJAIL:
                if os.path.isfile(src):
                    copy_file(src, relative_dst)
                else:
                    copy_tree(src, relative_dst)
            else:
                os.symlink(src, relative_dst)

    def _exec_run(self, command, **kwargs):
        # Set pyenv dir, otherwise it will detect the original pyenv which is inaccessible
        command = 'PYENV_DIR={} {}'.format(self.path, command)
        # Wrap with firejail
        if settings.VirtualEnv.USE_FIREJAIL:
            network = '' if self.network else ' --net=none'
            command = 'firejail{} --private-dev --private={} --quiet bash -c "{}"'.format(network, self.path, command)
        return exec(command)

    def exec_run(self, command, **kwargs):
        # detect and replace absolute path with get_path
        command = self.replace_abspath(command)
        # Run command
        command = 'PYENV_VERSION={} pyenv exec {}'.format(self.name, command)
        # Return results & error code
        return self._exec_run(command)

    def kill(self):
        pass

    def remove(self):
        # Delete virtualenv
        self._exec_run('pyenv uninstall -f {}'.format(self.name))
        # Move out of working dir
        os.chdir(settings.BASE_PATH)
        # Delete working dir
        print("Delete: {}".format(self.path))
        shutil.rmtree(self.path, ignore_errors=True) # DANGEROUS!!!


class Containers(object):
    def create(self, image, **kwargs):
        return Container(settings.VirtualEnv.PYTHON_VERSION, **kwargs)


class Client(object):
    def __init__(self):
        self.images = Images()
        self.containers = Containers()
        self.networks = Networks()


def init():
    TMP_SHARED_PATH = os.path.join(ROOT_PATH, 'shared_tmp')
    DEL_SHARED_PATH = os.path.join(ROOT_PATH, 'shared_del')
    print('>>> Link:', settings.VirtualEnv.SHARED_PATH, SHARED_PATH)
    # Copy to temporary path
    print('Copying:', settings.VirtualEnv.SHARED_PATH, TMP_SHARED_PATH)
    copy_tree(settings.VirtualEnv.SHARED_PATH, TMP_SHARED_PATH)
    # Move shared path to the del path
    print('Moving:', SHARED_PATH, DEL_SHARED_PATH)
    shutil.move(SHARED_PATH, DEL_SHARED_PATH)
    # Move tmp shared path to the proper path
    print('Moving:', TMP_SHARED_PATH, SHARED_PATH)
    shutil.move(TMP_SHARED_PATH, SHARED_PATH)
    # Delete original shared path
    print('Deleting:', DEL_SHARED_PATH)
    shutil.rmtree(DEL_SHARED_PATH, ignore_errors=True)

if __name__ == "__main__":
    init()