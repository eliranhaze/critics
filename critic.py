import cPickle as pkl
import os
import re

from bs4 import BeautifulSoup as bs
from datetime import datetime, timedelta
from scipy.stats.stats import pearsonr
from urlparse import urljoin

from utils.fetch import Fetcher
from films import FILMS, get_film_urls, get_film_name

from utils.logger import get_logger
logger = get_logger('critics')

BASE_URL = 'http://www.metacritic.com'
MIN_NUM_FILMS = 8
MIN_SCORE_AVG = 3
MAX_SCORE_AVG = 9.5
MIN_SCORES_RANGE = 2

class Cache(object):

    PKL = '.critics.pkl'
    PKL_FILMS = '.films.pkl'
    data = None

    @classmethod
    def get(cls):
        if cls.data is None:
            cls.load()
        return cls.data

    @classmethod
    def load(cls):
        logger.debug('loading data')
        if os.path.exists(cls.PKL) and os.path.exists(cls.PKL_FILMS):
            last_films = pkl.load(open(cls.PKL_FILMS, 'rb'))
            if last_films == FILMS:
                data = pkl.load(open(cls.PKL, 'rb'))
                logger.debug('data unchanged')
                cls.data = data

    @classmethod
    def save(cls, data):
        logger.debug('creating a new data')
        pkl.dump(data, open(cls.PKL, 'wb'))
        pkl.dump(FILMS, open(cls.PKL_FILMS, 'wb'))
        logger.debug('new data created')
        cls.data = data

class Metacritic(object):

    def __init__(self):
        self.critics = {}

    def get_critics(self):
	cache = Cache.get()
	if cache:
	    return cache
        fetcher = Fetcher(cache=True, cache_ttl=timedelta(days=365), refetch_prob=0.005)
        responses = fetcher.multi_fetch(get_film_urls(), timeout=180)
        for r in responses:
            self.extract_critics(r.content, get_film_name(r.url))
	Cache.save(self.critics)
        return self.critics

    def extract_critics(self, html, film):
        soup = bs(minify(html))
        reviews = findall(soup, 'div', 'class', 'review')
        num = 0
        for review in reviews:
            critic = self._parse_critic(review, film)
            if critic:
                num += 1
        logger.debug('processed %d critics for %s' % (num, film))

    def get_films(self, years, min_score):
        films = []
        cur_year = datetime.now().year
        for year in years:
            cache_ttl = timedelta(days = (cur_year - year + 1) * 10)
            fetcher = Fetcher(cache=True, cache_ttl=cache_ttl, processor=minify)
            url = urljoin(BASE_URL, '/browse/movies/score/metascore/year/filtered?year_selected=%d&sort=desc' % year)
            html = fetcher.fetch(url).content
            films.extend(self.extract_films(html, min_score))
        return films

    def extract_films(self, html, min_score):
        films = []
        soup = bs(html)
        links = findall(soup, 'a', 'class', 'metascore_anchor')
        for link in links:
            film = urljoin(BASE_URL, link.get('href'))
            score_div = find(link, 'div', 'class', 'metascore_w')
            if score_div:
                score = int(score_div.text)
                if score >= min_score:
                    films.append(film)
                else:
                    break
            else:
                logger.warning('%s has no score' % film)
        return films

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

def critic_minify(self, content):
    content = minify(content)
    content = re.sub('<div class="review_body">[\s\S]*?</div>', '', content)
    return content

class Critic(object):

    fetcher = Fetcher(cache=True, cache_ttl=timedelta(days=90), processor=critic_minify)

    def __init__(self, source, name, url):
        self.source = source
        self.name = name
        self.ident = _ident(source, name)
        self.url = url
        self.reviews = {}
        self.correlation = None

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
                logger.info('filtered out: %s avg %.1f rng %.1f num %d' % (self, scores_avg, scores_rng, len(critic_scores)))

    def get_all_reviews(self):
        reviews = {}
        for soup in self.gen_review_pages():
            reviews.update(self.extract_reviews(soup))
        logger('processed %d reviews: %s' % (len(reviews), self.ident))
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

    def __eq__(self, other):
        if type(other) is type(self):
            return self.ident == other.ident
        return False

    def __hash__(self):
        return hash(self.ident)

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
        a = e.find('a')
        if a:
            return a.get('href')

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

