# Reference: https://stackoverflow.com/a/601168

import signal
import time
from contextlib import contextmanager

class TimeoutException(Exception): pass

@contextmanager
def time_limit(seconds):
    if seconds:
        def signal_handler(signum, frame):
            raise TimeoutException("Timed out!")
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