import config
import json
from pprint import pprint
from slackclient import SlackClient
from http.server import *

global wx
global sc

class WeChat(object):

    def __init__(self, callback):
        self.msg_parsers = {}
        self.msg_parsers[1] = self._parse_text_msg
        self.cb = callback
        self.contacts = {}

    def register_msg_parser(self, msg_type, parser):
        self.msg_parsers[msg_type] = parser

    def _mod_contacts(self, data):
        for entry in data['ModContactList']:
            self.contacts[entry['UserName']] = entry
        pprint(self.contacts)

    def _get_contact_nickname(self, username):
        if username in self.contacts:
            return self.contacts[username]['NickName']
        else:
            return "NA"

    def _get_contact_displayname(self, username):
        try:
            return self.contacts[username]['DisplayName']
        except KeyError:
            return None

    def _parse_text_msg(self, msg):
        return "{}: {}".format(
            self._get_contact_displayname(msg['FromUserName']) or self._get_contact_nickname(msg['FromUserName']),
            msg['Content']
        )

    def handle_webwxsync(self, data):

        pprint(data)
        for msg in data['AddMsgList']:
            if msg['MsgType'] in self.msg_parsers:
                content = self.msg_parsers[msg['MsgType']](msg)
                self.cb(content)
        # update contacts
        if data['ModContactCount'] > 0:
            self._mod_contacts(data)

    def handle_webwxbatchgetcontact(self, data):

        #pprint(data)
        print("Adding {} contacts".format(len(data['ContactList'])))
        for entry in data['ContactList']:
            self.contacts[entry['UserName']] = entry
        print("{} contacts".format(len(self.contacts)))



class MyHTTPHandler(BaseHTTPRequestHandler):

    def do_POST(self):
        body = self.rfile.read(int(self.headers['Content-Length']))
        data = json.loads(body)

        try:
            if self.path.startswith('/webwxbatchgetcontact'):
                wx.handle_webwxbatchgetcontact(data)
            elif self.path.startswith('/webwxsync'):
                wx.handle_webwxsync(data)
        except (ValueError, KeyError) as e:
            print(e)

        self.send_response(200, "OK")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(b"{\"status\": 0}\r\n")


def post_message(text):
    print(sc.api_call(
        "chat.postMessage",
        channel=config.channel,
        text=text
    ))

if __name__ == "__main__":
    sc = SlackClient(config.slack_token)
    wx = WeChat(post_message)
    httpd = HTTPServer(config.server_address, MyHTTPHandler)
    httpd.serve_forever()
