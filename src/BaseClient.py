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


class BaseClient:
    def __init__(self, ip='127.0.0.1', port=8000, encryption=True):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((ip, port))
        self.echo()
        buffer.set_origin_ip(ip)

    def echo(self):
        with open(r"C:\Users\ahuma\Desktop\Programming\Networking\SocketServer\tests\test_file.txt", 'r') as f:
            data = f.read()
        while True:
            buffer.send_all(data, self.sock)
            received = buffer.unpack_data(buffer.recv_all(self.sock))
            print(f"RECEIVED_DATA: {received}\n LENGTH: {len(received['request_body'])}")
            time.sleep(15)
