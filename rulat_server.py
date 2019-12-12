"""
./rulat_server.py -l localhost -p 8000 -v 2
"""
import argparse
import requests
import io
from fetcher import fetch_page
from http.server import HTTPServer, BaseHTTPRequestHandler
from dicts import letters_v1, letters_v2, other

headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) ' 
					  'AppleWebKit/537.11 (KHTML, like Gecko) '
					  'Chrome/23.0.1271.64 Safari/537.11',
		'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
		'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
		'Accept-Encoding': 'none',
		'Accept-Language': 'en-US,en;q=0.8',
		'Connection': 'keep-alive'}

letters = dict()

class S(BaseHTTPRequestHandler):
	def data(self):
		if not self.path:
			url_main = 'https://ru.wikipedia.org/wiki/%D0%97%D0%B0%D0%B3%D0%BB%D0%B0%D0%B2%D0%BD%D0%B0%D1%8F_%D1%81%D1%82%D1%80%D0%B0%D0%BD%D0%B8%D1%86%D0%B0'
		else:
			url_main = 'https://ru.wikipedia.org' + self.path

		fetch_page(url_main, 'index.html', letters)
		return io.open('index.html', 'r', encoding='utf8', newline='\n').read()

	def _set_headers(self):
		self.send_response(200)
		self.send_header("Content-type", "text/html")
		self.end_headers()

	def _html(self, message):
		content = self.data()
		return content.encode('utf-8')

	def do_GET(self):
		self._set_headers()
		self.wfile.write(self._html("hi!"))
		print("#############################This is a path", str(self.path))

	def do_HEAD(self):
		self._set_headers()

	def do_POST(self):
		self._set_headers()
		self.wfile.write(self._html("POST!"))


def run(version, server_class=HTTPServer, handler_class=S, addr="localhost", port=8000):
	global letters
	assert (version < 3 ), "There are only two versions of romanisation right now."
	assert (version > 0 ), "There are only two versions of romanisation right now."
	if version == 1:
		letters = letters_v1
	elif version == 2:
		letters = letters_v2
	else:
		print("Assert, wtf")

	server_address = (addr, port)
	httpd = server_class(server_address, handler_class)

	print(f"Starting httpd server on {addr}:{port}")
	httpd.serve_forever()

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Run a simple HTTP server")
	parser.add_argument(
		"-l",
		"--listen",
		default="localhost",
		help="Specify the IP address on which the server listens",
	)
	parser.add_argument(
		"-p",
		"--port",
		type=int,
		default=8000,
		help="Specify the port on which the server listens",
	)
	parser.add_argument(
		"-v",
		"--version",
		type=int,
		default=1,
		help="Specify the version of romanisation type",
	)
	args = parser.parse_args()
	run(addr=args.listen, port=args.port, version = args.version)
