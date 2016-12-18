import random
import requests
import time
import urlparse

from executor import Executor

session = requests.Session()
session.headers['User-Agent'] = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.87 Safari/537.36'

executor = Executor(num_workers=12)

def _is_valid_url(url):
    parse = urlparse.urlparse(url)
    return parse.scheme and parse.netloc

def fetch(url, **kwargs):
    if not _is_valid_url(url):
        return
    try:
        while True:
            response = session.get(url, **kwargs)
            if int(response.status_code) == 429:
                print 'got %s, slowing down' % response
                time.sleep(1 + (random.random() * 3))
                continue
            return response
    except requests.exceptions.ConnectionError:
        time.sleep(1)
    except requests.exceptions.TooManyRedirects:
        return

def multi_fetch(urls, timeout, verify=False, **kwargs):
    task = lambda url: fetch(url, verify=verify, **kwargs)
    return executor.execute(task, urls, timeout)
