import re
import requests
#import base64
from http.server import BaseHTTPRequestHandler, HTTPServer

CLASH_URL = "https://dingyueieurwly.iajsy.lol/api/v1/client/subscribe?token=54fdd0a0458e2b7d6b3a0f06390d3bfe&security=a3b7fbbce2345d777"

class HTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if re.search('/get_jc/*', self.path):
            resp = requests.get("http://127.0.0.1:25500/sub?target=clash&url=%s" % CLASH_URL)
            #with open("/home/lo/.ns/text.txt", "wb") as f:
            #    f.write(resp.content)
            if resp.status_code == 200:
                #res = base64.b64decode(resp.content)
                res = resp.content
                self.send_response(200)
                self.send_header('Content-type','text/plain; charset=utf-8')
                self.send_header('Content-length', str(len(res)))
                self.end_headers()
                self.wfile.write(res)
            else:
                self.send_response(405, 'get proxy failed')
        else:
            self.send_response(403, 'unsupported func')
        self.end_headers()

if __name__ == '__main__':
    server = HTTPServer(('192.168.1.3', 8000), HTTPRequestHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()
