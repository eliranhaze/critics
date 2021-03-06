from urlparse import urljoin
import re

BASE_URL = 'http://www.metacritic.com/movie/'
URL_SUFFIX = 'critic-reviews'

# films with my ratings
FILMS = {

    # the best i've seen
    'the-wild-pear-tree': 10,
    'the-salesman': 10,
    'ida': 10,
    'a-separation': 10,
    'leviathan-2014': 10,
    'loveless-2017': 10,
    'gett-the-trial-of-viviane-amsalem': 10,
    'rams': 10,
    '4-months-3-weeks-and-2-days': 10,
    'winter-sleep': 9.5,
    'once-upon-a-time-in-anatolia': 9.5,
    'there-will-be-blood': 9.5,
    'carol': 9.5,
    'moonlight-2016': 9.5,

    # very good
    'son-of-saul': 9,
    'spring-summer-fall-winter-and-spring': 9,
    'the-pianist': 9,
    'pans-labyrinth': 9,
    'toni-erdmann': 9,
    'a-fantastic-woman': 9,
    'on-body-and-soul': 9,
    'phantom-thread': 9,
    'the-square-2017': 9,

    # kubrick
    'dr-strangelove-or-how-i-learned-to-stop-worrying-and-love-the-bomb': 9,
    '2001-a-space-odyssey': 10,
    'a-clockwork-orange': 9,
    'full-metal-jacket': 8,
    'eyes-wide-shut': 8,

    # woody
    'annie-hall-1977': 9.5,
    'manhattan': 9,
    'hannah-and-her-sisters': 9,
    'crimes-and-misdemeanors': 8.5,

    # kar-wai
    'days-of-being-wild-re-release': 8.5,
    'chungking-express': 9.5,
    'fallen-angels': 9,
    'happy-together': 8.8,
    'in-the-mood-for-love': 10,

    # personal favorites
    'amelie': 9,
    'american-beauty': 9,
    'the-lord-of-the-rings-the-fellowship-of-the-ring': 9,
    'the-lord-of-the-rings-the-two-towers': 9,
    'the-lord-of-the-rings-the-return-of-the-king': 9,
    'ray': 9,

    # documentaries
    'tempestad': 10,
    'the-thin-blue-line': 8,
    'the-fog-of-war-eleven-lessons-from-the-life-of-robert-s-mcnamara': 8.5,
    'the-central-park-five': 9.5,

    # worth watching
    'the-white-ribbon': 8.5,
    'paterson': 8.5,
    'lost-in-translation': 8.5,
    'the-master': 8.5,
    'brooklyn': 8.5,
    'sideways': 8.5,
    'gosford-park': 8.5,
    'the-postmans-white-nights': 8.5,
    'amour': 8.5,
    'the-lives-of-others': 8.5,
    'persepolis': 8.5,
    'fargo': 8.5,
    '12-years-a-slave': 8.5,
    'schindlers-list': 8.5,
    'borat-cultural-learnings-of-america-for-make-benefit-glorious-nation-of-kazakhstan': 8.5,
    'capote': 8.5,
    'no-country-for-old-men': 8.5,
    'manchester-by-the-sea': 8.5,
    'graduation': 8.5,
    'brokeback-mountain': 8.5,
    'the-salt-of-the-earth': 8.5,
    'the-other-side-of-hope': 8.5,
    'ray-liz': 8.5,
    'rosmarys-baby': 8,
    'brazil': 8,
    'her': 8,
    'about-elly-2009': 8,
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
    'dheepan': 8,
    'embrace-of-the-serpent': 8,
    'the-shape-of-water': 8,
    'gravity': 7.5,
    'me-and-earl-and-the-dying-girl': 7.5,
    'the-end-of-the-tour': 7.5,
    '45-years': 7.5,
    'blue-jasmine': 7.5,
    'happy-end': 7.5,
    'three-billboards-outside-ebbing-missouri': 7.5,
    'dogman': 7.5,
    'dead-poets-society': 7.5,

    # ok
    'eternal-sunshine-of-the-spotless-mind': 7,
    'boyhood': 7,
    'inherent-vice': 7,
    'birdman-or-the-unexpected-virtue-of-ignorance': 7,
    'up': 7,
    'children-of-men': 7,
    'what-we-do-in-the-shadows': 7,
    'avatar': 7,
    'sweet-bean': 7,
    'midnight-in-paris': 7,
    'captain-fantastic': 7, 
    'mommy': 7,
    'django-unchained': 7,
    'zero-dark-thirty': 7,
    'inside-out-2015': 7,
    'disobedience': 6.5,
    'sully': 6.5,
    'waking-life': 6.5,
    'paris-je-taime': 6.5,
    'the-dark-knight': 6.5,
    'the-dark-knight-rises': 6,
    'batman-begins': 6,
    'inglourious-basterds': 6,
    'inception': 6,
    'the-immigrant': 6,
    'blackkklansman': 6,

    # not worth it
    'the-incredibles': 5,
    'last-flag-flying': 5,
    'gangs-of-new-york': 5,
    'the-hobbit-an-unexpected-journey': 5,
    'the-sixth-sense': 5,
    'superman-returns': 5,
    'sicario': 5,
    'rocknrolla': 4,
    'the-academy-of-muses': 4,
    'the-hangover': 2,
    'the-hangover-part-ii': 2,
    'american-wedding': 2,
    'crazy-stupid-love': 2,
    '2-fast-2-furious': 2,
    'the-nice-guys': 2,
    'the-dukes-of-hazzard': 2,
    'gone-in-sixty-seconds': 2,
    'anaconda': 2,
    'the-wedding-planner': 2,
    'ghost-rider': 1,
}

def name_to_url(name):
    return _add_suffix(urljoin(BASE_URL, name))

def url_to_name(url):
    return re.findall('%s(\S+)/%s' % (BASE_URL, URL_SUFFIX), url.lower())[0]

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
