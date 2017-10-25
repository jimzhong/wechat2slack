import config
import json
import re
from bs4 import BeautifulSoup
from pprint import pprint
from slackclient import SlackClient
from http.server import *

global wx
global sc

FORWARDING_GROUP_NAMES = config.groups

def debug(url, body):

    for x in FORWARDING_GROUP_NAMES:
        if x in body:
            print("{} IN {}".format(x, url))
            print(x)

class WeChat(object):

    GROUP_MSG_REGEX = re.compile(r"^(@[0-9a-f]+):<br/>(.*)")

    def __init__(self, callback):
        self.msg_parsers = {}
        self.msg_parsers[1] = self._parse_text_msg
        self.cb = callback
        self.contacts = {}
        self.groups = {}

    def _get_contacts_nickname(self, username):
        if username in self.contacts:
            return self.contacts[username]['NickName']
        else:
            return None

    def _get_contacts_display_name(self, username):
        try:
            return self.contacts[username]['DisplayName']
        except KeyError:
            return None

    def _get_group_name(self, group_username):
        try:
            return self.groups[group_username]['NickName']
        except KeyError:
            return None

    def _get_group_member_nickname(self, group_username, member_username):
        try:
            return self.groups[group_username]['MemberDict'][member_username]['NickName']
        except KeyError:
            return self._get_contacts_nickname(member_username)

    def _get_group_member_display_name(self, group_username, member_username):
        try:
            return self.groups[group_username]['MemberDict'][member_username]['DisplayName']
        except KeyError:
            return self._get_contacts_display_name(member_username)


    def _parse_text_msg(self, msg):

        parts = self.GROUP_MSG_REGEX.match(msg['Content'])

        if parts is None:
            # individual messages
            # do nothing
            return
        else:
            # from a group
            data = {}
            try:
                soup = BeautifulSoup(parts[2], "html.parser")
            except:
                print("Message content parsing error")
                return
            data['content'] = soup.get_text()
            data['group_name'] = self._get_group_name(msg['FromUserName'])
            data['member_nickname'] = self._get_group_member_nickname(msg['FromUserName'], parts[1])
            data['member_display_name'] = self._get_group_member_display_name(msg['FromUserName'], parts[1])
            return data

    def _handle_group_update(self, entry):

        print("Got group {}, containing {} members".format(entry['NickName'],
            len(entry['MemberList'])))

        key = entry['UserName']

        try:
            self.groups[key].update(entry)
        except KeyError:
            self.groups[key] = entry

        # dict for fast mapping from username to NickName, DisplayName
        d = {}
        for member in entry['MemberList']:
            try:
                d[member['UserName']].update(member)
            except KeyError:
                d[member['UserName']] = member

        try:
            self.groups[key]['MemberDict'].update(d)
        except KeyError:
            self.groups[key]['MemberDict'] = d

    def _handle_contact_update(self, entry):
        try:
            key = entry['UserName']
        except KeyError:
            return
        if key.startswith('@@'):
            self._handle_group_update(entry)
        else:
            try:
                # update that contact entry if it exists
                # allow incremental updates
                self.contacts[key].update(entry)
            except KeyError:
                self.contacts[key] = entry


    def handle_webwxsync(self, data):

        # update contacts
        if data['ModContactCount'] > 0:
            for entry in data['ModContactList']:
                self._handle_contact_update(entry)

        for msg in data['AddMsgList']:
            if msg['MsgType'] in self.msg_parsers:
                data = self.msg_parsers[msg['MsgType']](msg)
                self.cb(data)

    def handle_webwxbatchgetcontact(self, data):

        print("Adding {} contacts".format(len(data['ContactList'])))
        for entry in data['ContactList']:
            self._handle_contact_update(entry)

    def handle_webwxgetcontact(self, data):

        print("Adding {} contacts".format(data["MemberCount"]))

        for entry in data["MemberList"]:
            self._handle_contact_update(entry)



class MyHTTPHandler(BaseHTTPRequestHandler):

    def do_POST(self):
        body = self.rfile.read(int(self.headers['Content-Length'])).decode('utf-8', 'replace')
        self.send_response(200, "OK")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        try:
            data = json.loads(body)
        except ValueError:
            self.wfile.write(b"Error\r\n")
            # ignore non json responses
            return

        path = self.path.replace("/cgi-bin/mmwebwx-bin/", "")

        try:
            if path.startswith('webwxbatchgetcontact'):
                wx.handle_webwxbatchgetcontact(data)
            elif path.startswith('webwxsync'):
                wx.handle_webwxsync(data)
            elif path.startswith('webwxgetcontact'):
                wx.handle_webwxgetcontact(data)
        except (ValueError, KeyError, IndexError) as e:
            print(e)

        self.wfile.write(b"OK\r\n")


    def do_GET(self):

        self.send_response(200, "OK")
        self.send_header("Content-Type", "application/json")
        self.end_headers()

        resp = '{"error": "not found"}'

        if self.path.startswith('/contacts'):
            resp = json.dumps(wx.contacts)
        elif self.path.startswith('/groups'):
            resp = json.dumps(wx.groups)

        self.wfile.write((resp + "\r\n").encode())


def post_message(message_dict):
    if message_dict is None:
        return

    try:
        message_text = "{member_nickname} in {group_name}: {content}".format(**message_dict)
        if message_dict['member_display_name']:
            message_text = "{member_display_name}({member_nickname}) in {group_name}: {content}".format(**message_dict)
    except KeyError:
        return

    if message_dict['group_name'] in FORWARDING_GROUP_NAMES:
        sc.api_call("chat.postMessage", channel=config.channel, text=message_text)
        print("Forwarded message:", message_text)

if __name__ == "__main__":
    sc = SlackClient(config.slack_token)
    wx = WeChat(post_message)
    httpd = HTTPServer(config.server_address, MyHTTPHandler)
    httpd.serve_forever()
