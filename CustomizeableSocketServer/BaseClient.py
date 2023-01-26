import selectors
import socket
import json
from typing import Optional, Union, IO
from pydantic import BaseModel
import logging
import time
import sys
import ssl
from schemas import SchemaProducer
from SocketOperations import BaseSocketOperator, Connection
import SocketOperations
import getpass


class BaseClient(BaseSocketOperator, SchemaProducer):
    def __init__(self, ip: str='192.168.0.161', port: int=8000, buffer_size: int=4096):
        self.set_buffer_size(buffer_size)

        self.sock: IO = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((ip, port))

        self.sock = ssl.wrap_socket(self.sock, ssl_version=ssl.PROTOCOL_SSLv23)

        self.connection = Connection(ip, self.sock, socket.gethostbyaddr(ip))

class AdminClient(BaseClient):
    def submit_password

    
    
