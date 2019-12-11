import io
import requests
from dicts import letters, other

headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) ' 
                      'AppleWebKit/537.11 (KHTML, like Gecko) '
                      'Chrome/23.0.1271.64 Safari/537.11',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
        'Accept-Encoding': 'none',
        'Accept-Language': 'en-US,en;q=0.8',
        'Connection': 'keep-alive'}

url = 'https://ru.wikipedia.org/wiki/%D0%AF%D0%BF%D0%BE%D0%BD%D0%B8%D1%8F'

def fetch_page(url, page_name = 'page.html'):
	res = requests.get(url, headers=headers)
	res.raise_for_status()
	html = res.text

	rep = (
		('src="//','src="https://'),
		('srcset="//','srcset="https://'),
		('<link rel="stylesheet" href="/w/', 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'),
		('href="https://ru.wikipedia.org/:','bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb'),
		('href="','href="http://localhost:8000/'),
		('bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb','href="http://localhost:8000/'),
		('aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa', '<link rel="stylesheet" href="https://ru.wikipedia.org//w/'),
		('8000//','8000/'))

	for _r in rep:
		html = html.replace(_r[0],_r[1])

	for _o in other.items():
		html = html.replace(_o[0],_o[1])

	for _k in letters.items():
		html = html.replace(_k[0],_k[1])

	with io.open(page_name, 'w', encoding='utf8', newline='\n') as fout:
		fout.write(html)

if __name__ == "__main__":
	fetch_page(url)