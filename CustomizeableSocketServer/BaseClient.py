import selectors
import socket
from typing import Optional, Union, IO
import ssl
from SocketOperations import BaseSocketOperator
import SocketOperations
import selectors
import logging


class BaseClient(BaseSocketOperator):
    def __init__(self, ip: str=SocketOperations.LOCALHOST, port: int=8000, buffer_size: int=4096, log_dir: str | None=None):
        if log_dir:
            self.__logger = logging.getLogger(__name__)

            c_handler = logging.StreamHandler()
            c_handler.setLevel(logging.INFO)
            f_handler = logging.FileHandler(log_dir)
            f_handler.setLevel(logging.INFO)

            c_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            c_handler.setFormatter(c_format)
            f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            f_handler.setFormatter(f_format)

            self.__logger.addHandler(c_handler)
            self.__logger.addHandler(f_handler)

        self.set_buffer_size(buffer_size)
        self.received = []
        self.connection = None
        my_hostname = socket.gethostname()
        self.my_ip = socket.gethostbyname(my_hostname)
        
        self.ip = ip
        self.port = port
        self.sock: IO = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sel = selectors.DefaultSelector()

        self.connect_to_server(self.ip, self.port)

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
        frag_data, agg_data = self.recv_all(self.connection)
        self.received.append(agg_data)
        print(agg_data)
        

class AdminClient(BaseClient):
    def submit_password(self, password):
        auth_message = self.construct_authentication_body(self.my_ip, self.ip, password)
        self.send_all(auth_message, self.connection)

    

    
    
