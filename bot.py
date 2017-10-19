import config
import json
from pprint import pprint
from slackclient import SlackClient
from http.server import *

global wx
wx = None

class WeChat(object):

    def __init__(self, sc, ch):
        self.msg_parsers = {}
        self.msg_parsers[1] = self.parse_text_msg
        self.sc = sc
        self.ch = ch

    def post_message(self, text):
        print(self.sc.api_call(
            "chat.postMessage",
            channel=self.ch,
            text=text
        ))

    def register_msg_parser(self, msg_type, parser):
        self.msg_parsers[msg_type] = parser

    def parse_text_msg(self, msg):
        return msg['Content']

    def handle_webwxsync(self, text):
        data = json.loads(text)
        pprint(data)
        for msg in data['AddMsgList']:
            if msg['MsgType'] in self.msg_parsers:
                content = self.msg_parsers[msg['MsgType']](msg)
                self.post_message(content)


class MyHTTPHandler(BaseHTTPRequestHandler):

    def do_POST(self):
        try:
            body = self.rfile.read(int(self.headers['Content-Length']))
            wx.handle_webwxsync(body)
        except (IOError, ValueError):
            raise

        self.send_response(200, "OK")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(b"OK\r\n")

if __name__ == "__main__":
    sc = SlackClient(config.slack_token)
    wx = WeChat(sc, config.channel)
    httpd = HTTPServer(config.server_address, MyHTTPHandler)
    httpd.serve_forever()
