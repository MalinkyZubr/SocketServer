import selectors
import socket
import json
from typing import Optional, Union
from pydantic import BaseModel
import logging
import time
import sys
import ssl
from schemas import BaseSchema
from buffer import buffer
from Connection import Connection


class BaseClient:
    def __init__(self, ip: str, port=8000):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((ip, port))

        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.load_verify_locations()

        with context.wrap_socket(self.sock, server_hostname=ip) as ssock:
            self.sock = ssock
        self.connection = Connection(ip, self.sock, socket.gethostbyaddr(ip))

    def echo(self, data):
        while True:
            buffer.send_all(data, self.sock)
            received = buffer.unpack_data(buffer.recv_all(self.sock))
            print(f"RECEIVED_DATA: {received}\n LENGTH: {len(received['request_body'])}")
            time.sleep(15)

    
