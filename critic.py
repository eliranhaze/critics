from bs4 import BeautifulSoup as bs
from datetime import timedelta
from scipy.stats.stats import pearsonr
from urlparse import urljoin

import re

from utils.fetch import Fetcher

BASE_URL = 'http://www.metacritic.com'
MIN_NUM_FILMS = 8
MIN_SCORE_AVG = 3
MAX_SCORE_AVG = 9
MIN_SCORES_RANGE = 4

class Metacritic(object):

    def __init__(self):
        self.critics = {}

    def extract_critics(self, html, film):
        soup = bs(minify(html))
        reviews = findall(soup, 'div', 'class', 'review')
        num = 0
        for review in reviews:
            critic = self._parse_critic(review, film)
            if critic:
                num += 1
        #print 'processed %d critics for %s' % (num, film)

    def _get_critic(self, name, source):
        ident = _ident(source, name)
        return self.critics.get(ident)

    def _parse_critic(self, soup, film):
        name =_get_author(soup)
        source = _get_source(soup)
        critic = self._get_critic(name, source)
        if critic is None:
            critic = Critic.from_soup(film, soup, source, name)
            if critic is not None:
                self.critics[critic.ident] = critic
        else:
            critic.parse_review(film, soup)
        return critic

class Critic(object):

    def __init__(self, source, name, url):
        self.source = source
        self.name = name
        self.ident = _ident(source, name)
        self.url = url
        self.reviews = {}
        self.correlation = None
        self.fetcher = Fetcher(cache=True, cache_ttl=timedelta(days=90), refetch_prob=0.005, processor=self._minify)

    @classmethod
    def from_soup(cls, film, soup, source, name):
        if not name and not source:
            return None
        path = _get_path(soup)
        critic = cls(
            source = source,
            name = name,
            url = urljoin(BASE_URL, path) if path else None,
        )
        critic.add_review(film, _get_score(soup))
        return critic

    def parse_review(self, film, soup):
        self.add_review(film, _get_score(soup))

    def add_review(self, film, score):
        self.reviews[film] = score

    def correlate(self, films):
        critic_scores = []
        films_scores = []
        for film, score in self.reviews.iteritems():
            critic_scores.append(score)
            films_scores.append(films[film])
        if len(critic_scores) >= MIN_NUM_FILMS:
            scores_avg = sum(critic_scores)/len(critic_scores)
            scores_rng = max(critic_scores)-min(critic_scores)
            if MIN_SCORE_AVG <= scores_avg <= MAX_SCORE_AVG and scores_rng >= MIN_SCORES_RANGE:
                self.correlation = pearsonr(critic_scores, films_scores)[0]
            else:
                pass # TODO: use logger
                #print 'filtered out: %s avg %.1f rng %.1f num %d' % (self, scores_avg, scores_rng, len(critic_scores))

    def get_all_reviews(self):
        reviews = {}
        for soup in self.gen_review_pages():
            reviews.update(self.extract_reviews(soup))
        print 'processed %d reviews: %s' % (len(reviews), self.ident)
        return reviews

    def gen_review_pages(self):
        # first page
        url = '%s&num_items=100&sort_options=critic_score' % self.url
        response = self.fetcher.fetch(url)
        if response:
            soup = bs(response.content)
            yield soup
            # other_page
            urls = []
            for elem in findall(soup, 'li', 'class', 'page'):
                a = elem.find('a')
                if a:
                    path = a.get('href')
                    urls.append(urljoin(BASE_URL, path))
            for response in self.fetcher.multi_fetch(urls, timeout=180):
                if response:
                    yield bs(response.content)

    def extract_reviews(self, soup):
        reviews = findall(soup, key='class', value='critic_review')
        result = {}
        for review in reviews:
            film_url = urljoin(BASE_URL, review.find('a').get('href'))
            score_elem = find(review, key='class', value='brief_critscore')
            score = _get_score(score_elem)
            result[film_url] = score
        return result

    def _minify(self, content):
        content = minify(content)
        content = re.sub('<div class="review_body">[\s\S]*?</div>', '', content)
        return content

    def __eq__(self, other):
        if type(other) is type(self):
            return self.ident == other.ident
        return False

    def __str__(self):
        return '%s [%.2f] (%d)' % (self.ident, self.correlation if self.correlation else 0, len(self.reviews))

    __repr__ = __str__

# utils

def _get_source(soup):
    e = find(soup, key='class', value='source')
    if e:
        return e.text

def _get_author(soup):
    e = find(soup, key='class', value='author')
    if e:
        return e.text.split(';').pop()

def _get_score(soup):
    return float(find(soup, key='class', value='metascore_w').text) / 10.

def _get_path(soup):
    e = find(soup, key='class', value='author')
    if e:
        return e.find('a').get('href')

def _ident(source, author):
    return '%s/%s' % (source, author)

def findall(soup, name=None, key=None, value=None):
    found = soup.find_all(name)
    return [x for x in found if key is None or value in x.get(key, [])]

def find(soup, name=None, key=None, value=None):
    found = findall(soup, name, key, value)
    return found[0] if found else None

def minify(content):
    content = re.sub('<footer[\s\S]*?</footer>', '', content)
    content = re.sub('<nav[\s\S]*?</nav>', '', content)
    content = re.sub('<script[\s\S]*?</script>', '', content)
    content = re.sub('<form[\s\S]*?</form>', '', content)
    content = re.sub('<style[\s\S]*?</style>', '', content)
    content = re.sub('<h[1-6][\s\S]*?</h[1-6]>', '', content)
    content = re.sub('<!--[\s\S]*?-->', '', content)
    content = re.sub('style=".*?"', ' ', content)
    content = re.sub('src=".*?"', ' ', content)
    content = re.sub('target=".*?"', ' ', content)
    content = ' '.join(content.split())
    return content

