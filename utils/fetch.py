"""
fetching and caching utility

note: master version is at words project, until moved to a different repo
"""

from collections import namedtuple
from datetime import datetime, timedelta
from threading import RLock

import os
import random
import re
import requests
import time
import urlparse

from executor import Executor

from logger import get_logger
logger = get_logger('fetch')

requests.packages.urllib3.disable_warnings()

DEFAULT_TIMEOUT = 10 # seconds

#########################################################
# utils

CONTENT_TYPES = {
    'text/html',
    'text/plain',
    'text/xml',
    'xml',
    'application/rss+xml',
    'application/json',
    'application/xml',
}

def _is_valid_url(url):
    try:
        parse = urlparse.urlparse(url)
        return parse.scheme and parse.netloc
    except:
        return False

def _is_ok_content_type(response):
    content_type = response.headers.get('Content-Type')
    if content_type:
        content_type = content_type.split(';')[0]
        return content_type in CONTENT_TYPES
    return False

#########################################################
# main objects

Response = namedtuple('Response', ['url', 'content'])

class Fetcher(object):

    def __init__(self, cache=False, cache_ttl=None, refetch_prob=0, processor=None):
        self.cache = Cache(cache_ttl) if cache else None
        self.refetch_prob = refetch_prob
        self.processor = processor
        self.executor = Executor(num_workers=12)
        self._init_session()

    def _init_session(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.87 Safari/537.36',
        })

    def _request_until_success(self, url, verify=False, **kwargs):
        max_attempts = 3
        attempt = 0
        while True:
            attempt += 1
            if attempt > max_attempts:
                logger.warning('giving up on %s', url)
                return
            try:
                logger.debug('request %s attempt=%d', url, attempt)
                kwargs.setdefault('timeout', DEFAULT_TIMEOUT)
                response = self.session.get(url, verify=False, **kwargs)
                logger.debug('response %s size=%.2fkb elapsed=%.1fms',
                    response.url, len(response._content)/1024., response.elapsed.total_seconds() * 1000.)
                if not _is_ok_content_type(response):
                    logger.warning('skipping content type %s (%s)', response.url, response.headers.get('Content-Type'))
                    return
                if int(response.status_code) == 429:
                    logger.debug('got %s, slowing down %s', response, url)
                    time.sleep(attempt)
                    continue
                if not response.ok:
                    logger.warning('response %s not ok: status code %d', response.url, response.status_code)
                return response
            except requests.exceptions.ConnectionError, e:
                logger.error('got error %s (%d): %r' % (url, attempt, e))
                time.sleep(attempt)
            except requests.exceptions.TooManyRedirects, e:
                logger.error('got error %s (%d): %r' % (url, attempt, e))
                return
            except Exception, e:
                logger.error('unhandled %s (%d): %r' % (url, attempt, e))
                return

    def _get_cached(self, url, params=None):
        if self.cache and random.random() >= self.refetch_prob:
            cached = self.cache.get(url, params)
            if cached:
                logger.debug('retrieved %s from cache', url)
                return Response(url=url, content=cached)

    #==============================================
    # main functions 
    #==============================================

    def fetch(self, url, **kwargs):
        logger.debug('fetching %s', url)
        if not _is_valid_url(url) and _is_valid_url('http://' + url):
            url = 'http://' + url
        if not _is_valid_url(url):
            logger.debug('url %r is not valid', url)
            return
        params = kwargs.get('params')
        cached = self._get_cached(url, params)
        if cached:
            return cached
        response = self._request_until_success(url, **kwargs)
        if response:
            content = self.processor(response.content) if self.processor else response.content
            if self.cache:
                self.cache.put(content, url, params)
            return Response(url=response.url, content=content)
        logger.warning('fetch: got none (url=%s)' % url)

    def multi_fetch(self, urls, timeout=300, **kwargs):
        task = lambda url: self.fetch(url, **kwargs)
        return self.executor.execute(task, urls, timeout)

class Cache(object):

    lock = RLock()

    cache_dir = '.cache'
    metafile = '%s/%s' % (cache_dir, '.metadata')
    sep = ' # '

    def __init__(self, cache_ttl=None):
        self.cache_ttl = cache_ttl
        self._init_cache_dir()

    #==============================================
    # internal read-write
    #==============================================

    def _init_cache_dir(self):
        with self.lock:
            if not os.path.exists(self.cache_dir):
                os.makedirs(self.cache_dir)
            if not os.path.exists(self.metafile):
                open(self.metafile,'a').close()

    def create_entry_path(self, entry):
        with self.lock:
            with open(self.metafile, 'a+') as f:
                f.seek(0) # move to start of file for reading
                lines = f.read().splitlines()
                name = int(lines[-1].split(self.sep)[-1])+1 if lines else 0
                f.write('%s%s%s\n' % (entry, self.sep, name))
                return '%s/%s' % (self.cache_dir, name)

    def get_entry_path(self, entry, create=False):
        lookfor = '%s%s' % (entry, self.sep)
        with self.lock:
            with open(self.metafile) as f:
                for line in f.read().splitlines():
                    if line.startswith(lookfor):
                        name = line.split(self.sep)[-1]
                        return '%s/%s' % (self.cache_dir, name)
            # not found
            if create:
                return self.create_entry_path(entry)

    #==============================================
    # internal utilities
    #==============================================

    def to_entry(self, url, params=None):
        url = re.sub('[^\w\s-]', '', url)
        params = self.params_to_string(params)
        return '%s%s' % (url, params)

    def build_path(self, url, params, create=False):
        return self.get_entry_path(self.to_entry(url, params), create=create)

    def params_to_string(self, params):
        name = ''
        if params:
            for k, v in params.iteritems():
                name += '%s%s' % (k, v)
        return name

    def is_cached(self, url, params=None):
        path = self.build_path(url, params)
        if path and os.path.exists(path):
            age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(path))
            if not self.cache_ttl or age < self.cache_ttl:
                return True
        return False

    #==============================================
    # main functions 
    #==============================================

    def get(self, url, params=None):
        if self.is_cached(url, params):
            path = self.build_path(url, params)
            with open(path) as cached:
                return cached.read()

    def put(self, content, url, params=None):
        path = self.build_path(url, params, create=True)
        with open(path, 'w') as out:
           out.write(content)

#########################################################
# defaults

fetcher = Fetcher(cache=True, cache_ttl=timedelta(days=30))

def fetch(*args, **kwargs):
    return fetcher.fetch(*args, **kwargs)

def multi_fetch(*args, **kwargs):
    return fetcher.multi_fetch(*args, **kwargs)

#########################################################
