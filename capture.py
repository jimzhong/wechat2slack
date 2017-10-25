from urllib.parse import urlsplit
import requests

SERVER_URL = "http://127.0.0.1:1234"

FORWARD_CONTENT_TYPES = ('text/javascript', 'application/json', 'text/plain')

def response(flow):

    url = urlsplit(flow.request.url)
    content_type = flow.response.headers.get('Content-Type')
    if content_type not in FORWARD_CONTENT_TYPES:
        return
    if url.netloc.endswith("wx2.qq.com"):
        try:
            requests.post(SERVER_URL + url.path, flow.response.content)
        except:
            print("POST error")
