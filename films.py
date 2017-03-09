from urlparse import urljoin

BASE_URL = 'http://www.metacritic.com/movie/'
URL_SUFFIX = 'critic-reviews'

# films with my ratings
FILMS = {

     # the best i've seen
    'ida': 10,
    'in-the-mood-for-love': 10,
    'a-separation': 10,
    'leviathan-2014': 10,
    'gett-the-trial-of-viviane-amsalem': 10,
    'rams': 10,
    '4-months-3-weeks-and-2-days': 10,
    'winter-sleep': 9.5,
    'once-upon-a-time-in-anatolia': 9.5,
    'there-will-be-blood': 9.5,
    'carol': 9.5,
    'son-of-saul': 9,
    'spring-summer-fall-winter-and-spring': 9,
    'chungking-express': 9,
    'the-pianist': 9,

    # kubrick
    'dr-strangelove-or-how-i-learned-to-stop-worrying-and-love-the-bomb': 9,
    '2001-a-space-odyssey': 10,
    'a-clockwork-orange': 9,
    'full-metal-jacket': 8,
    'eyes-wide-shut': 8,

    # personal favorites
    'amelie': 9,
    'american-beauty': 9,
    'the-lord-of-the-rings-the-fellowship-of-the-ring': 9,
    'the-lord-of-the-rings-the-two-towers': 9,
    'the-lord-of-the-rings-the-return-of-the-king': 9,
    'ray': 9,
    'eternal-sunshine-of-the-spotless-mind': 9,

    # worth watching
    'sideways': 8.5,
    'gosford-park': 8.5,
    'the-postmans-white-nights': 8.5,
    'amour': 8.5,
    'the-lives-of-others': 8.5,
    'persepolis': 8.5,
    'fargo': 8.5,
    'pans-labyrinth': 8.5,
    '12-years-a-slave': 8.5,
    'schindlers-list': 8.5,
    'borat-cultural-learnings-of-america-for-make-benefit-glorious-nation-of-kazakhstan': 8.5,
    'capote': 8.5,
    'no-country-for-old-men': 8.5,
    'manchester-by-the-sea': 8.5,
    'graduation': 8.5,
    'brokeback-mountain': 8.5,
    'crimes-and-misdemeanors': 8,
    'brazil': 8,
    'her': 8,
    'about-elly-2009': 8,
    'the-salt-of-the-earth': 8,
    'the-tale-of-the-princess-kaguya': 8,
    'victoria': 8,
    'wild-tales': 8,
    'nebraska': 8,
    'anomalisa': 8,
    'magnolia': 8,
    'a-pigeon-sat-on-a-branch-reflecting-on-existence': 8,
    'the-lobster': 8,
    'the-grand-budapest-hotel': 8,
    'lincoln': 8,
    'the-return-2004': 8,
    'inside-llewyn-davis': 8,
    'into-the-wild': 8,
    'ratatouille': 8,
    'a-very-long-engagement': 8,
    'wall-e': 8,
    'the-social-network': 8,
    'sand-storm': 8,
    'after-the-storm-2016': 8,
    'april-and-the-extraordinary-world': 8,
    'spotlight': 8,
    'beyond-the-hills': 8,
    'gravity': 7.9,
    'me-and-earl-and-the-dying-girl': 7.8,
    'the-end-of-the-tour': 7.5,

    # ok
    'what-we-do-in-the-shadows': 7,
    'avatar': 7,
    'sweet-bean': 7,
    'blue-valentine': 7,  
    'midnight-in-paris': 7,
    'captain-fantastic': 7, 
    'mommy': 7,
    'django-unchained': 7,
    'zero-dark-thirty': 7,
    'sully': 7,
    'inside-out-2015': 7, 
    'paris-je-taime': 6.5,
    'the-dark-knight': 6.5,
    'the-dark-knight-rises': 6,

    # not worth it
    'the-sixth-sense': 5,
    'superman-returns': 5,
    'sicario': 5,
    'the-academy-of-muses': 4,
    'the-hangover': 3,
    'the-hangover-part-ii': 2,
    'american-wedding': 2,
    'crazy-stupid-love': 2,
    '2-fast-2-furious': 2,
    'the-nice-guys': 2,
}

def name_to_url(name):
    return _add_suffix(urljoin(BASE_URL, name))

def _add_suffix(url):
    return '%s/%s' % (url, URL_SUFFIX)

NAME_BY_URL = {
    name_to_url(k): k for k in FILMS.iterkeys()
}
URL_BY_NAME = {
    v: k for k, v in NAME_BY_URL.iteritems()
}

def get_film_urls():
    return NAME_BY_URL.keys()

def get_film_name(url):
    return NAME_BY_URL.get(url)

def film_exists(name=None, url=None):
    if name:
        return name in FILMS
    if url:
        if not url.endswith(URL_SUFFIX):
            url = _add_suffix(url)
        return url in NAME_BY_URL
    return False
