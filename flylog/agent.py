#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
用来作为接受log传递的agent
通过udp通道。
"""

import json
import functools
import logging
import logging.config
import socket
import threading
import SocketServer
import signal
import sys
import time
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formatdate

import constants


class ThreadedUDPRequestHandler(SocketServer.BaseRequestHandler):

    def _configure_mail_host(self):
        mail_client = None

        if self.server.config.MAIL_USE_SSL:
            mail_client = smtplib.SMTP_SSL(self.server.config.MAIL_SERVER, self.server.config.MAIL_PORT)
        else:
            mail_client = smtplib.SMTP(self.server.config.MAIL_SERVER, self.server.config.MAIL_PORT)

        mail_client.set_debuglevel(self.server.debug)

        if self.server.config.MAIL_USE_TLS:
            mail_client.starttls()

        if self.server.config.MAIL_USERNAME and self.server.config.MAIL_PASSWORD:
            mail_client.login(self.server.config.MAIL_USERNAME, self.server.config.MAIL_PASSWORD)

        return mail_client

    def _handle_message(self, message):
        recv_dict = json.loads(message)
        mail_msg = MIMEText(recv_dict.get('content'), 'plain', 'utf-8')
        mail_msg['Subject'] = Header(u'[%s]Attention!' % recv_dict.get('source'), 'utf-8')
        mail_msg['From'] = self.server.config.MAIL_SENDER
        mail_msg['To'] = ', '.join(self.server.config.MAIL_RECEIVER_LIST)
        mail_msg['Date'] = formatdate()

        # 发邮件
        mail_client = self._configure_mail_host()
        mail_client.sendmail(self.server.config.MAIL_SENDER, self.server.config.MAIL_RECEIVER_LIST, mail_msg.as_string())
        mail_client.quit()

    def handle(self):
        message = self.request[0]
        self.server.logger.debug("message, len: %s, content: %s", len(message), message)
        try:
            self._handle_message(message)
        except Exception, e:
            self.server.logger.error('exception occur. e: %s', e)


class FlyLogAgent(SocketServer.ThreadingUDPServer):
    debug = False

    def __init__(self, host=None, port=None, config=None, log_name=None):
        # 因为父类继承是用的老风格，所以必须按照下面的方式来写。 不能使用 super(GAAgent, self).__init__
        SocketServer.ThreadingUDPServer.__init__(self,
                                                 (host or constants.FLY_LOG_AGENT_HOST,
                                                  port or constants.FLY_LOG_AGENT_PORT),
                                                 ThreadedUDPRequestHandler)
        self.logger = logging.getLogger(log_name or constants.FLY_LOG_AGENT_LOG_NAME)
        self.config = config

    def run(self):
        server_thread = threading.Thread(target=self.serve_forever)
        # Exit the server thread when the main thread terminates
        server_thread.daemon = True
        server_thread.start()

        # 因为daemon设置为true，所以不做while循环会直接退出
        # 而之所以把 daemon 设置为true，是为了防止进程不结束的问题
        while True:
            time.sleep(1)
