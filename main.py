import requests

from critic import Critic, Metacritic
from films import FILMS

MIN_CORRELATION = 0.4
MIN_FILM_REVIEWS = 6
MIN_FILM_SCORE = 8.5

session = requests.Session()
session.headers['User-Agent'] = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.87 Safari/537.36'

def get_metacritic():
    meta = Metacritic()
    for url in FILMS:
        critics_url = '%s/critic-reviews' % url
        meta.extract_critics(session.get(critics_url).content, url)
    return meta

def correlate(critics):
    correlated = []
    for critic in critics:
        critic.correlate(FILMS)
        correlated.append(critic)
    return correlated

def main():
    print '### GETTING CRITICS ###'
    metacritic = get_metacritic()
    print '### CORRELATING ###'
    critics = correlate(metacritic.critics.itervalues())
    filtered_critics = [c for c in critics if c.correlation >= MIN_CORRELATION]
    filtered_critics.sort(key=lambda c: -c.correlation)
    print '### MY CRITICS (%d out of %d) ###' % (len(filtered_critics), len(critics))
    for critic in filtered_critics:
        print critic
    print '### RECOMMENDING FILMS ###'
    films = {}
    for critic in filtered_critics:
        all_reviews = critic.get_all_reviews(fetcher=lambda x: session.get(x).content)
        if all_reviews:
            for film, score in all_reviews.iteritems():
                scores = films.setdefault(film, [])
                scores.append(score)
    sorted_films = [
        (film, float(sum(scores))/len(scores))
        for film, scores in films.iteritems()
        if len(scores) >= MIN_FILM_REVIEWS and film not in FILMS
    ]
    sorted_films = [(f, score) for f, score in sorted_films if score >= MIN_FILM_SCORE]
    sorted_films.sort(key=lambda x: -x[1])
    for film, score in sorted_films:
        print '%s, %.1f' % (film, score)

if __name__ == '__main__':
    main()
