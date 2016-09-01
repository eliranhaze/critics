from BeautifulSoup import BeautifulSoup
from scipy.stats.stats import pearsonr
from urlparse import urljoin

BASE_URL = 'http://www.metacritic.com'
MIN_NUM_FILMS = 7

class Metacritic(object):

    def __init__(self):
        self.critics = {}

    def extract_critics(self, html, film):
        soup = BeautifulSoup(html)
        reviews = soup.findAll('li', {'class': lambda x: x is not None and 'review critic_review' in x})
        print 'extracting', len(reviews), soup.find('title').text
        for review in reviews:
            ident = Critic.ident_from_soup_li(review)
            critic = self.critics.get(ident, None)
            if not critic:
                critic = Critic.from_soup_li(film, review)
                self.critics[critic.ident] = critic
            else:
                critic.add_review_li(film, review)

class Critic(object):

    def __init__(self, source, name, url):
        self.source = source
        self.name = name
        self.url = url
        self.reviews = {}
        self.correlation = None

    @classmethod
    def from_soup_li(cls, film, li):
        path = _get_path(li)
        critic = cls(
            source = _get_source(li),
            name = _get_author(li),
            url = urljoin(BASE_URL, path) if path else None,
        )
        critic.add_review(film, _get_score(li))
        return critic

    @classmethod
    def ident_from_soup_li(cls, li):
        return _ident(_get_source(li), _get_author(li))

    @property
    def ident(self):
        return _ident(self.source, self.name)

    def add_review_li(self, film, li):
        self.add_review(film, _get_score(li))

    def add_review(self, film, score):
        self.reviews[film] = score

    def correlate(self, films):
        critic_scores = []
        films_scores = []
        for film, score in self.reviews.iteritems():
            critic_scores.append(score)
            films_scores.append(films[film])
        if len(critic_scores) >= MIN_NUM_FILMS:
            self.correlation = pearsonr(critic_scores, films_scores)[0]

    def get_all_reviews(self, fetcher):
        if self.url:
            reviews = {}
            url = '%s&num_items=100&sort_options=critic_score' % self.url
            # first page
            html = fetcher(url)
            reviews.update(self.extract_reviews(fetcher(url)))
            soup = BeautifulSoup(html)
            # other pages
            urls = [urljoin(BASE_URL, li.find('a').get('href')) for li in soup.findAll('li', {'class': 'page'})]
            for url in urls:
                reviews.update(self.extract_reviews(fetcher(url)))
            return reviews

    def extract_reviews(self, html):
        soup = BeautifulSoup(html)
        reviews = soup.findAll('li', {'class': lambda x: 'review critic_review' in x})
        print 'extracting', len(reviews), soup.find('title').text
        result = {}
        for review in reviews:
            film = urljoin(BASE_URL, review.find('a').get('href'))
            score_li = review.find('li', {'class': lambda x: 'brief_critscore' in x})
            score = _get_score(score_li, elem='span')
            #gen_score = _get_score(review.find('li', {'class': lambda x: 'brief_metascore' in x}), elem='span')
            result[film] = score
        return result

    def __str__(self):
        return '%s [%.3f] (%d)' % (self.ident, self.correlation, len(self.reviews))

    __repr__ = __str__

# utils

def _get_source(li, elem='div'):
    return li.find(elem, {'class': 'source'}).text

def _get_author(li):
    return li.find('div', {'class': 'author'}).text.split(';').pop()

def _get_score(li, elem='div'):
    return float(li.find(elem, {'class': lambda x: 'metascore_w' in x}).text) / 10.

def _get_path(li):
    author_li = li.find('li', {'class': lambda x: 'author_reviews' in x})
    if author_li:
        return author_li.find('a').get('href')

def _ident(source, author):
    return '%s/%s' % (source, author)
