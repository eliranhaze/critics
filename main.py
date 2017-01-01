from datetime import timedelta

import argparse
import requests

from critic import Critic, Metacritic
from films import FILMS, get_film_urls, get_film_name, film_exists
from utils.fetch import Fetcher

# default params
MIN_CORRELATION = 0.5
MIN_FILM_REVIEWS = 5
MIN_FILM_SCORE = 8.5

fetcher = Fetcher(cache=True, cache_ttl=timedelta(days=365), refetch_prob=0.01)

def get_metacritic():
    meta = Metacritic()
    responses = fetcher.multi_fetch(get_film_urls(), timeout=180)
    for r in responses:
        meta.extract_critics(r.content, get_film_name(r.url))
    return meta

def correlate(critics):
    correlated = []
    for critic in critics:
        critic.correlate(FILMS)
        correlated.append(critic)
    return correlated

def get_critics(min_corr):
    metacritic = get_metacritic()
    critics = correlate(metacritic.critics.itervalues())
    filtered_critics = [c for c in critics if c.correlation >= min_corr] 
    filtered_critics.sort(key=lambda c: -c.correlation)
    return critics, filtered_critics

def recommend_films(critics, min_reviews, min_score):
    films = {}
    cur = 0
    for critic in critics:
        cur += 1
        print 'visiting critic %d/%d' % (cur, len(critics))
        all_reviews = critic.get_all_reviews()
        if all_reviews:
            for film, score in all_reviews.iteritems():
                scores = films.setdefault(film, [])
                scores.append(score)
    sorted_films = [
        (film_url, float(sum(scores))/len(scores))
        for film_url, scores in films.iteritems()
        if len(scores) >= min_reviews and not film_exists(url=film_url)
    ]
    sorted_films = [(f, score) for f, score in sorted_films if score >= min_score]
    sorted_films.sort(key=lambda x: -x[1])
    return sorted_films

def main():
    # args
    args = get_args()
    min_corr = args.min_corr if args.min_corr else MIN_CORRELATION
    min_reviews = args.min_reviews if args.min_reviews else MIN_FILM_REVIEWS
    min_score = args.min_score if args.min_score else MIN_FILM_SCORE
    recommend = not args.no_rec
    ##########################################

    print '### GETTING CRITICS ###'
    all_critics, filtered_critics = get_critics(min_corr)
    print '### TOP CRITICS (%d out of %d) ###' % (len(filtered_critics), len(all_critics))
    for critic in filtered_critics:
        print critic

    if recommend:
        print '### RECOMMENDING FILMS ###'
        films = recommend_films(filtered_critics, min_reviews, min_score)
        print '### RECOMMENDATIONS ###'
        for film, score in films:
            print '%s, %.1f' % (film, score)

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--min-cor', dest='min_corr', type=float)
    parser.add_argument('--min-rev', dest='min_reviews', type=float)
    parser.add_argument('--min-scr', dest='min_score', type=float)
    parser.add_argument('--no-rec', dest='no_rec', action='store_true')
    args = parser.parse_args()
    return args

if __name__ == '__main__':
    main()
