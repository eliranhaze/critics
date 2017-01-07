"""
fetching and caching utility

note: master version is at words project, until moved to a different repo
"""

from collections import namedtuple
from datetime import datetime, timedelta

import os
import random
import re
import requests
import time
import urlparse

from executor import Executor

requests.packages.urllib3.disable_warnings()

#########################################################
# utils

def _is_valid_url(url):
    parse = urlparse.urlparse(url)
    return parse.scheme and parse.netloc

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
        attempt = 0
        while True:
            attempt += 1
            try:
                # TODO: maybe create session everytime? check times
                response = self.session.get(url, verify=False, **kwargs)
                if int(response.status_code) == 429:
                    print 'got %s, slowing down' % response
                    time.sleep(attempt)
                    continue
                return response
            except requests.exceptions.ConnectionError, e:
                print 'got error (%d): %r' % (attempt, e)
                time.sleep(attempt)
            except requests.exceptions.TooManyRedirects:
                return
            except Exception, e:
                print 'unhandled (%d): %r' % (attempt, e)
                return

    def _get_cached(self, url, params=None):
        if self.cache and random.random() >= self.refetch_prob:
            cached = self.cache.get(url, params)
            if cached:
                return Response(url=url, content=cached)

    #==============================================
    # main functions 
    #==============================================

    def fetch(self, url, **kwargs):
        if not _is_valid_url(url):
            return
        params = kwargs.get('params')
        cached = self._get_cached(url, params)
        if cached:
            return cached
        response = self._request_until_success(url, **kwargs)
        if response:
            if self.cache:
                content = self.processor(response.content) if self.processor else response.content
                self.cache.put(content, url, params)
        else:
            print 'fetch: got none (url=%s)' % url
        return response

    def multi_fetch(self, urls, timeout=120, **kwargs):
        task = lambda url: self.fetch(url, **kwargs)
        return self.executor.execute(task, urls, timeout)

class Cache(object):

    cache_dir = '.cache'
    metafile = '%s/%s' % (cache_dir, '.metadata')
    sep = ' # '

    def __init__(self, cache_ttl=None):
        self.cache_ttl = cache_ttl
        self._init_cache_dir()

    def _init_cache_dir(self):
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
        if not os.path.exists(self.metafile):
            open(self.metafile,'a').close()

    def create_entry_path(self, entry):
        with open(self.metafile, 'a+') as f:
            lines = f.read().splitlines()
            name = int(lines[-1].split(self.sep)[-1])+1 if lines else 0
            f.write('%s%s%s\n' % (entry, self.sep, name))
            return '%s/%s' % (self.cache_dir, name)

    def get_entry_path(self, entry, create=False):
        lookfor = '%s%s' % (entry, self.sep)
        with open(self.metafile) as f:
            for line in f.read().splitlines():
                if line.startswith(lookfor):
                    name = line.split(self.sep)[-1]
                    return '%s/%s' % (self.cache_dir, name)
        # not found
        if create:
            return self.create_entry_path(entry)

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
