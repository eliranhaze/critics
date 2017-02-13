from bs4 import BeautifulSoup as bs

MIN_BIT_SIZE = 75

def extract_text(html=None, element=None):
    if element is None:
        element = bs(html)
    return ' '.join([p.text.strip() for p in element.findAll('p') if len(p.text.strip()) > MIN_BIT_SIZE])
