from datetime import timedelta

import argparse
import requests

from critic import Critic, Metacritic
from films import FILMS, get_film_name, film_exists, name_to_url, url_to_name
from utils.fetch import Fetcher

# default params
MIN_CORRELATION = 0.65
MIN_FILM_REVIEWS = 5
MIN_FILM_SCORE = 8.5

fetcher = Fetcher(cache=True, cache_ttl=timedelta(days=365), refetch_prob=0.005)

def correlate(critics):
    correlated = []
    for critic in critics:
        critic.correlate(FILMS)
        correlated.append(critic)
    return correlated

def get_critics(min_corr):
    uncorr_critics = Metacritic().get_critics()
    critics = correlate(uncorr_critics.itervalues())
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

def films_ratings(film_urls, filtered_critics):
    m = Metacritic()
    responses = fetcher.multi_fetch(film_urls, timeout=180)
    for r in responses:
        film = r.url
        m.extract_critics(r.content, film)
        criteria = {
            'top': lambda c: c in filtered_critics,
        }
        scores = []
        for critic in m.critics.itervalues():
            if film not in critic.reviews:
                continue
            if critic in filtered_critics:
                scores.append(critic.reviews[film])
        if scores:
            print '%s: %.1f' % (url_to_name(film), avg(scores))

def test_films():
    min_corr = MIN_CORRELATION
    print '### GETTING CRITICS ###'
    all_critics, filtered_critics = get_critics(min_corr)
    print '### TOP CRITICS (%d out of %d) ###' % (len(filtered_critics), len(all_critics))
    for critic in filtered_critics:
        print critic
    m = Metacritic()
    films = m.get_films(range(2013, 2018), 70)
    films_ratings(films, filtered_critics)

def avg(it):
    return sum(it)/len(it)

def wavg(w, x):
    return 1.*sum(wi*xi for wi,xi in zip(w,x))/sum(w)

def main():
    # args
    args = get_args()
    min_corr = args.min_corr if args.min_corr else MIN_CORRELATION
    min_reviews = args.min_reviews if args.min_reviews else MIN_FILM_REVIEWS
    min_score = args.min_score if args.min_score else MIN_FILM_SCORE
    recommend = not args.no_rec
    film = args.film
    ##########################################

    print '### GETTING CRITICS ###'
    all_critics, filtered_critics = get_critics(min_corr)
    print '### TOP CRITICS (%d out of %d) ###' % (len(filtered_critics), len(all_critics))
    for critic in filtered_critics:
        print critic

    critic_corrs = {c: c.correlation for c in all_critics}
    if film:
        m = Metacritic()
        m.extract_critics(fetcher.fetch(name_to_url(film)).content, film)
        criteria = {
            'all': lambda c: True,
            'top': lambda c: c in filtered_critics,
            '>0.50': lambda c: critic_corrs.get(c, 0) > 0.5,
            '>0.60': lambda c: critic_corrs.get(c, 0) > 0.6,
            '>0.65': lambda c: critic_corrs.get(c, 0) > 0.65,
            '>0.70': lambda c: critic_corrs.get(c, 0) > 0.70,
            '>0.75': lambda c: critic_corrs.get(c, 0) > 0.75,
        }
        scores = {}
        wscores = {}
        for critic in m.critics.itervalues():
            for label, criterion in criteria.iteritems():
                if criterion(critic):
                    scores.setdefault(label, []).append(critic.reviews[film])
                    critic_corr = critic_corrs.get(critic)
                    if critic_corr:
                        wscores.setdefault(label, []).append((critic_corr, critic.reviews[film]))
        print '### RATINGS FOR %s ###' % film.upper()
        for label, ratings in sorted(scores.iteritems()):
            if label in ('all', 'top'):
                print '%s: %.2f (%d)' % (label, avg(ratings), len(ratings))
        for label, wratings in sorted(wscores.iteritems()):
            if label not in ('all', 'top'):
                weights, ratings = zip(*wratings)
                print '%s-w: %.2f (%d)' % (label, wavg(weights, ratings), len(ratings))
        recommend = False
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
    parser.add_argument('--film', dest='film')
    args = parser.parse_args()
    return args

if __name__ == '__main__':
    main()
