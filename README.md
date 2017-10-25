# wechat2slack

Forwards wechat group messages to slack

## capture.py

For use with mitmdump. Run `mitmdump -s capture.py`. And then set your broswer's
HTTP proxy to `127.0.0.1:8080`. You can change the port with the `-p` option of
mitmdump.


## bot.py

Listens on given port. When receiving a text message from a group in the `groups`
 list in `config.py`, it sends that message to the slack channel specified in
  `config.py`. If you change the `server_address` in `config.py`, you should
  also edit `capture.py` accordingly.
