import selectors
import socket
import json
from typing import Optional, Union, IO
from pydantic import BaseModel
import logging
import time
import sys
import ssl
from schemas import BaseSchema
from SocketOperations import BaseSocketOperator, Connection
import SocketOperations


class BaseClient(BaseSocketOperator):
    def __init__(self, ip: str=SocketOperations.LOCALHOST, port: int=8000, buffer_size: int=4096):
        self.set_buffer_size(buffer_size)

        self.sock: IO = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((ip, port))

        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.load_verify_locations(capath=r'C:\Users\ahuma\Desktop\programming\Networking\SocketServer\ca.crt')

        with context.wrap_socket(self.sock, server_hostname=ip) as ssock:
            self.sock = ssock
        self.connection = Connection(ip, self.sock, socket.gethostbyaddr(ip))

    def send(self, package):
        data: list = self.__prepare_all(package)
        self.__send_all(data, self.connection)
    
