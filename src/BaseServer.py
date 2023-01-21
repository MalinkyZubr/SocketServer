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


class Client:
    def __init__(self, ip, conn, hostname):
        self.ip = ip
        self.conn = conn
        self.hostname = hostname

    def __str__(self):
        return f"""
        IP: {self.ip}
        HOSTNAME: {self.hostname}
        CONN: {self.conn}
                """


class BaseServer:
    def __init__(self, *args, ip='127.0.0.1', port=8000, encrypted=False, timeout=1000, schema=None, cert_dir=None, key_dir=None):
        self.connections = []
        self.functions = list(args)
        self.ip = ip
        self.port = port
        self.hostname = socket.gethostbyaddr(ip)
        self.sel = selectors.DefaultSelector()

        self.context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        self.context.load_cert_chain(cert_dir, key_dir)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(timeout)
        self.sock.setblocking(False)
        self.sock.bind((ip, port))
        self.sock.listen(10)
        buffer.set_buffer_server(True)

    def find_connection(self, target_ip: str) -> Client | bool:
        for connection in self.connections:
            if connection.ip == target_ip:
                return connection
            return False

    def receive_requests(self, connection: Client | None=None):
        print(connection.ip)
        fragmented_data, raw_data= buffer.recv_all(connection.conn)
        try:
            data = buffer.unpack_data(raw_data)
        except json.decoder.JSONDecodeError:
            self.sel.unregister(connection.conn)
            self.connections.remove(connection)
            return 0

        print(data)
        target_ip = data['destination_ip']
        target_connection = self.find_connection(target_ip=target_ip)
        buffer.send_all(fragmented_data, target_connection)
        
    def accept_connection(self):
        print("[!] awaiting connection request")
        with self.context.wrap_socket(self.sock, server_side=True) as ssock:
            conn, addr = ssock.accept()
        conn.setblocking(False)
        print("[+] connection established")
        client = Client(ip=addr[0], conn=conn, hostname=socket.gethostbyaddr(addr[0]))
        self.connections.append(client)
        self.sel.register(conn, selectors.EVENT_READ, lambda: self.receive_requests(connection=client))

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
