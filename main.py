import requests

from BeautifulSoup import BeautifulSoup
from scipy.stats.stats import pearsonr

from films import FILMS

MIN_CORRELATION = 0.35
MIN_NUM_FILMS = 5

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
    print 'extracting', len(reviews), soup.find('title').text
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
    nums = {}
    for critic, critic_films in critics.iteritems():
        critic_scores = []
        my_scores = []
        for film, score in critic_films.iteritems():
            critic_scores.append(score)
            my_scores.append(FILMS[film])
        num_films = len(my_scores)
        if num_films >= MIN_NUM_FILMS:
            correlation = pearsonr(critic_scores, my_scores)[0]
            if correlation >= MIN_CORRELATION :
                correlations[critic] = correlation
                nums[critic] = num_films
    return correlations, nums

def main():
    print '### GETTING CRITICS ###'
    critics = get_critics()
    print '### CORRELATING ###'
    correlations, nums = get_correlations(critics)
    sorted_critics = correlations.items()
    sorted_critics.sort(key=lambda x: -x[1])
    print '### RESULT ###'
    for critic, correlation in sorted_critics:
        print critic, correlation, '(%s)' % nums[critic]

if __name__ == '__main__':
    main()
