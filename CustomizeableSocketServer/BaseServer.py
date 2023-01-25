import selectors
import socket
import json
from typing import Optional, Union
import logging
import time
import sys
import ssl
from SocketOperations import BaseSocketOperator, Connection
import SocketOperations


class BaseServer(BaseSocketOperator):
    def __init__(self, ip: str='192.168.0.161', port: int=8000, timeout: int=1000, buffer_size: int=4096, cert_dir=None, key_dir=None):
        self.set_buffer_size(buffer_size)
        self.connections = []
        self.ip: str = ip
        self.port: int = port
        self.hostname: str = socket.gethostbyaddr(ip)
        self.sel = selectors.DefaultSelector()

        self.cert_dir = cert_dir
        self.key_dir = key_dir

        # Socket Setup
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(timeout)
        self.sock.setblocking(False)
        self.sock.bind((ip, port))
        self.sock.listen(10)

    def __find_connection(self, destination_ip: str) -> Connection | bool:
        for connection in self.connections:
            if connection.ip == destination_ip:
                return connection
            raise Exception("Connection not found")

    def process_requests(self, connection: Connection):
        try:
            frag_data, agg_data = self.recv_all(connection) 
            destination_ip = agg_data.get('destination_ip')
            destination_connection: Connection = self.__find_connection(destination_ip)
            self.__send_all(frag_data, destination_connection)
        except json.decoder.JSONDecodeError:
            self.sel.unregister(connection.conn)
            self.connections.remove(connection)
            print("fucked")
        
    def accept_connection(self):
        conn, addr = self.sock.accept()
        print("Connection Accepted")
        conn = ssl.wrap_socket(conn, ssl_version=ssl.PROTOCOL_SSLv23, server_side=True, certfile=self.cert_dir, keyfile=self.key_dir)
        conn.setblocking(False)
        connection = Connection(addr[0], conn, hostname=socket.gethostbyaddr(addr[0]))
        self.connections.append(connection)
        self.sel.register(conn, selectors.EVENT_READ, lambda: self.process_requests(connection=connection))
        print("Connection Started")

    def start(self):
        self.sel.register(self.sock, selectors.EVENT_READ, self.accept_connection)
        print(f"[+] Starting TCP server on {self.ip}:{self.port}")
        while True:
            events = self.sel.select()
            for key, mask in events:
                callback = key.data
                callback()

    def __str__(self):
        return f"""
        IP: {self.ip}
        PORT: {self.port}
        """
