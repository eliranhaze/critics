import requests

from BeautifulSoup import BeautifulSoup
from scipy.stats.stats import pearsonr

from films import FILMS

session = requests.Session()
session.headers['User-Agent'] = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.87 Safari/537.36'

def get_critics():
    critics = {}
    for url in FILMS:
        critics_url = '%s/critic-reviews' % url
        for critic, score in extract_reviews(session.get(critics_url).content).iteritems():
            critic_films = critics.setdefault(critic, {})
            critic_films[url] = score
    return critics    

def extract_reviews(html):
    soup = BeautifulSoup(html)
    reviews = soup.findAll('li', {'class': lambda x: 'review critic_review' in x})
    print 'extracting', len(reviews), 'from', soup.find('title').text
    result = {}
    for review in reviews:
        source = review.find('div', {'class': 'source'}).text
        author = review.find('div', {'class': 'author'}).text.split(';').pop()
        score = float(review.find('div', {'class': lambda x: 'metascore_w' in x}).text) / 10.
        result['%s/%s' % (source, author)] = score
        #print 'processed', source, author, score
    return result

def get_correlations(critics):
    correlations = {}
    for critic, critic_films in critics.iteritems():
        critic_scores = []
        my_scores = []
        for film, score in critic_films.iteritems():
            critic_scores.append(score)
            my_scores.append(FILMS[film])
        if len(my_scores) > 2:
            correlation = pearsonr(critic_scores, my_scores)[0]
            if correlation > 0:
                correlations[critic] = correlation
    return correlations

def main():
    print '### GETTING CRITICS ###'
    critics = get_critics()
    print '### CORRELATING ###'
    correlations = get_correlations(critics)
    sorted_critics = correlations.items()
    sorted_critics.sort(key=lambda x: -x[1])
    print '### RESULT ###'
    for critic, correlation in sorted_critics:
        print critic, correlation

if __name__ == '__main__':
    main()
