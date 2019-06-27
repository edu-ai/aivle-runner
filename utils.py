import secrets
import string
import hashlib

import signal
import time
from contextlib import contextmanager


def generate_secure_string(N):
	return ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(N))

def hash_file(file, block_size=65536):
    hasher = hashlib.md5()
    while True:
        data = file.read(block_size)
        if not data:
            break
        hasher.update(data)
    return hasher.hexdigest()


# Reference: https://stackoverflow.com/a/601168

class TimeoutException(Exception): pass

@contextmanager
def time_limit(seconds, message="Time limit exceeded"):
    if seconds:
        def signal_handler(signum, frame):
            raise TimeoutException(message)
        signal.signal(signal.SIGALRM, signal_handler)
        signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)

@contextmanager
def time_print(task_name):
    t = time.time()
    try:
        yield
    finally:
        print(task_name, "took", time.time() - t, "seconds.")