import utils
import settings
import os
import subprocess
import re
import shutil

def exec(command):
    p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    out, err = p.communicate()

    exit_code = 0
    output = out.decode('utf-8')
    if err:
        exit_code = 1
        output = err.decode('utf-8')

    return exit_code, output
    
  

class Network(object): # DUMMY
    def connect(self, container):
        pass

    def disconnect(self, container):
        pass


class Networks(object): # DUMMY
    def list(self):
        return [Network()]


class Image(object): # DUMMY
    def __init__(self):
        self.attrs = {}
        self.attrs['Size'] = 0


class Images(object): # DUMMY
    def pull(self, name):
        exec('pyenv install {}'.format(settings.VirtualEnv.PYTHON_VERSION))

    def get(self, name):
        return Image()

    def delete(self, name):
        pass


class Container(object):
    def __init__(self, image, **kwargs):
        self.image = image
        self.volumes = kwargs.get('volumes', {})
        self.name = kwargs.get('name', utils.generate_secure_string(16))
        self.path = os.path.join(settings.VirtualEnv.ROOT_PATH, self.name)

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
        # Create virtual environment
        exec('pyenv virtualenv {} {}'.format(self.image, self.name))
        # Create working folder and cd
        os.makedirs(self.path, exist_ok=True)
        os.chdir(self.path)
        # Symlink volumes to working folder
        for src, dst in self.volumes.items():
            relative_dst = self.get_path(dst['bind'])
            os.makedirs(os.path.dirname(relative_dst), exist_ok=True)
            try:
                os.remove(relative_dst)
            except:
                pass
            os.symlink(src, relative_dst)

    def exec_run(self, command, **kwargs):
        # detect and replace absolute path with get_path
        command = self.replace_abspath(command)
        # Run command
        command = 'PYENV_VERSION={} pyenv exec {}'.format(self.name, command)
        # Return results & error code
        return exec(command)

    def kill(self):
        pass

    def remove(self):
        # Delete virtualenv
        exec('pyenv uninstall {}'.format(self.name))
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