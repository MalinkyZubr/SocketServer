import selectors
import socket
from typing import Optional, Union, IO, Type
import ssl
from SocketOperations import BaseSocketOperator
import SocketOperations
import selectors
import logging
from schemas import BaseSchema
import os
import threading
logging.basicConfig(level=logging.INFO)


class BaseClient(BaseSocketOperator):
    def __init__(self, ip: str=SocketOperations.LOCALHOST, port: int=8000, buffer_size: int=4096, log_dir: str | None=None):
        self.logger = logging.getLogger("client")
        c_handler = logging.StreamHandler()
        c_handler.setLevel(logging.INFO)
        c_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        c_handler.setFormatter(c_format)
        self.logger.addHandler(c_handler)
        if log_dir:
            f_handler = logging.FileHandler(log_dir)
            f_handler.setLevel(logging.INFO)

            f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            f_handler.setFormatter(f_format)

            self.logger.addHandler(f_handler)

        self.set_buffer_size(buffer_size)
        self.received = []
        self.connection = None
        my_hostname = socket.gethostname()
        self.set_my_ip(socket.gethostbyname(my_hostname))
        
        self.ip = ip
        self.port = port
        self.sock: IO = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sel = selectors.DefaultSelector()

    def connect_to_server(self, ip, port):
        self.sock.connect((ip, port))
        self.sock = ssl.wrap_socket(self.sock, ssl_version=ssl.PROTOCOL_SSLv23)
        self.connection = self.construct_connection(str(socket.gethostbyaddr(ip)), str(ip), self.sock)
        self.sel.register(self.connection.conn, selectors.EVENT_READ, self.receive_messages)
        while True:
            events = self.sel.select()
            for key, mask in events:
                callback = key.data
                callback()

    def receive_messages(self):
        agg_data = self.recv_all(self.connection)
        self.received.append(agg_data)
        print(f'{agg_data}\n')

    def client_send(self, data: Type[BaseSchema]):
        self.send_all(data, self.connection)

    def command_line_input(self):
        while True:
            try:
                command = input("\n> ")
                message = self.construct_base_body(self.ip, command)
                self.client_send(message)
            except (EOFError, KeyboardInterrupt):
                self.sel.unregister(self.connection.conn)
                self.connection.conn.close()
                os._exit(0)
                
    def start_client_runtime(self):
        input_thread = threading.Thread(target=self.command_line_input)
        input_thread.start()
        self.connect_to_server(self.ip, self.port)
    

class AdminClient(BaseClient):
    def submit_password(self, password):
        auth_message = self.construct_authentication_body(self.my_ip, self.ip, password)
        self.client_send(auth_message)


    
    
