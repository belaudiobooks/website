from dataclasses import dataclass
from queue import Queue
from threading import Thread
from typing import List
import requests


class Worker(Thread):
    ''' Thread executing tasks from a given tasks queue '''

    def __init__(self, tasks):
        Thread.__init__(self)
        self.tasks = tasks
        self.daemon = True
        self.start()

    def run(self):
        while True:
            func, args, kargs = self.tasks.get()
            try:
                func(*args, **kargs)
            except Exception as exc:
                # An exception happened in this thread
                print(exc, args)
            finally:
                # Mark this task as done, whether an exception happened or not
                self.tasks.task_done()


@dataclass
class FetchResult:
    'Result of fetching url'
    url: str
    response: requests.Response


def fetch_head_urls(urls: List[str]) -> List[FetchResult]:
    '''Fetches list of provided urls using HEAD request.'''
    statuses: List[FetchResult] = []
    get = lambda url: statuses.append(
        FetchResult(url, requests.head(url, timeout=20)))
    tasks = Queue()
    for _ in range(10):
        Worker(tasks)

    for url in urls:
        tasks.put((get, (url, ), {}))
    tasks.join()
    return statuses