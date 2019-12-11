"""
./rulat-server.py -l localhost -p 8000
"""
import argparse
import requests
import io
from fetcher import fetch_page
from http.server import HTTPServer, BaseHTTPRequestHandler

headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) ' 
					  'AppleWebKit/537.11 (KHTML, like Gecko) '
					  'Chrome/23.0.1271.64 Safari/537.11',
		'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
		'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
		'Accept-Encoding': 'none',
		'Accept-Language': 'en-US,en;q=0.8',
		'Connection': 'keep-alive'}

class S(BaseHTTPRequestHandler):
	def data(self):
		if not self.path:
			url_main = 'https://ru.wikipedia.org/wiki/%D0%97%D0%B0%D0%B3%D0%BB%D0%B0%D0%B2%D0%BD%D0%B0%D1%8F_%D1%81%D1%82%D1%80%D0%B0%D0%BD%D0%B8%D1%86%D0%B0'
		else:
			url_main = 'https://ru.wikipedia.org' + self.path

		fetch_page(url_main, 'index.html')
		return io.open('index.html', 'r', encoding='utf8', newline='\n').read()

	def _set_headers(self):
		self.send_response(200)
		self.send_header("Content-type", "text/html")
		self.end_headers()

	def _html(self, message):
		"""This just generates an HTML document that includes `message`
		in the body. Override, or re-write this do do more interesting stuff.
		"""
		
		#content = f"<html><body><h1>{message}</h1></body></html>"
		# content = requests.get(url, headers=headers)
		# content.raise_for_status()
		content = self.data()
		#fetch_page('https://ru.wikipedia.org' + self.path)
		
		# self._data = io.open('page.html', 'r', encoding='utf8', newline='\n').read

		# return content.text.encode('utf-8')  # NOTE: must return a bytes object!
		return content.encode('utf-8')
	def do_GET(self):
		self._set_headers()
		self.wfile.write(self._html("hi!"))
		print("#############################This is a path", str(self.path))

	def do_HEAD(self):
		self._set_headers()

	def do_POST(self):
		# Doesn't do anything with posted data
		self._set_headers()
		self.wfile.write(self._html("POST!"))


def run(server_class=HTTPServer, handler_class=S, addr="localhost", port=8000):

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
	args = parser.parse_args()
	run(addr=args.listen, port=args.port)