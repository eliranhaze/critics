import re

def minify_feed(content):
    content = content.replace('<description/>','').replace('<media:description/>','').replace('<content:encoded/>','').replace('<category/>','')
    content = re.sub('<description[ >][\s\S]*?</description>', '', content)
    content = re.sub('<media:description[ >][\s\S]*?</media:description>', '', content)
    content = re.sub('<content:encoded[ >][\s\S]*?</content:encoded>', '', content)
    content = re.sub('<category[ >][\s\S]*?</category>', '', content)
    return content

def minify_html(content):
    content = re.sub('<footer[\s\S]*?</footer>', '', content)
    content = re.sub('<nav[\s\S]*?</nav>', '', content)
    content = re.sub('<script[\s\S]*?</script>', '', content)
    content = re.sub('<form[\s\S]*?</form>', '', content)
    content = re.sub('<style[\s\S]*?</style>', '', content)
    content = re.sub('<h[1-6][\s\S]*?</h[1-6]>', '', content)
    content = re.sub('<!--[\s\S]*?-->', '', content)
    content = re.sub('href=".*?"', ' ', content)
    content = re.sub('style=".*?"', ' ', content)
    content = re.sub('src=".*?"', ' ', content)
    content = content.replace('  ',' ').replace('\n\n','\n')
    return content

