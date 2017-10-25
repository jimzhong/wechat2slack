from urllib.parse import urlsplit
import requests

SERVER_URL = "http://127.0.0.1:1234"

def response(flow):

    url = urlsplit(flow.request.url)
    headers = flow.response.headers
    pprint(headers)
    if url.netloc.endswith("wx2.qq.com"):
        try:
            requests.post(SERVER_URL + url.path, flow.response.content)
        except:
            print("POST error")
