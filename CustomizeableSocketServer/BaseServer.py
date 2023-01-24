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


class BaseServer:
    def __init__(self, ip='127.0.0.1', port=8000, encrypted=False, timeout=1000, schema=None, cert_dir=None, key_dir=None):
        self.connections = []
        self.ip = ip
        self.port = port
        self.hostname = socket.gethostbyaddr(ip)
        self.sel = selectors.DefaultSelector()

        # SSL Setup
        self.context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        self.context.load_cert_chain(cert_dir, key_dir)

        # Socket Setup
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(timeout)
        self.sock.setblocking(False)
        self.sock.bind((ip, port))
        self.sock.listen(10)

    def __find_connection(self, target_ip: str) -> Connection | bool:
        for connection in self.connections:
            if connection.ip == target_ip:
                return connection
            raise Exception("Connection not found")

    def process_requests(self, connection: Connection):
        try:
            frag_data, agg_data = buffer.recv_all(connection.conn) # 
        except json.decoder.JSONDecodeError:
            self.sel.unregister(connection.conn)
            self.connections.remove(connection)

        target_ip = agg_data.get('destination_ip')
        try:    
            target_connection: Connection = self.__find_connection(target_ip=target_ip)
            buffer.send_all(frag_data, target_connection) # add function to return error to origin Connection
        except Exception as e:
            print("Destination address not found")
        
    def accept_connection(self):
        with self.context.wrap_socket(self.sock, server_side=True) as ssock:
            conn, addr = ssock.accept()
        conn.setblocking(False)

        connection = Connection(ip=addr[0], conn=conn, hostname=socket.gethostbyaddr(addr[0]))
        self.connections.append(connection)
        self.sel.register(conn, selectors.EVENT_READ, lambda: self.process_requests(connection=Connection))

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
