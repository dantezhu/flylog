# -*- coding: utf-8 -*-

__version__ = '0.2.6'

from .api.log_handler import LogHandler
from .api.client import Client
from .server.server import Server

# 向下兼容
FlyLogHandler = LogHandler
