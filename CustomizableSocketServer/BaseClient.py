import selectors
import socket
from typing import IO, Type
import ssl
from . import SocketOperations
from . import schemas
import selectors
import logging
import os
import threading
logging.basicConfig(level=logging.INFO)


class BaseClient(SocketOperations.BaseSocketOperator):
    def __init__(self, ip: str=SocketOperations.LOCALHOST, port: int=8000, buffer_size: int=4096, log_dir: str | None=None):
        self.create_logger(log_dir=log_dir)
        self.set_type_client()
        self.set_buffer_size(buffer_size)
        self.received = []
        self.connection = None
        my_hostname = socket.gethostname()
        self.set_my_ip(socket.gethostbyname(my_hostname))
        
        self.ip = ip
        self.port = port
        self.sock: IO = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sel = selectors.DefaultSelector()

    def client_send_all(self, data: Type[schemas.BaseSchema]):
        data = self.__prepare_all(data)
        for fragment in data: 
            self.connection.conn.send(fragment)

    def connect_to_server(self):
        self.sock.connect((self.ip, self.port))
        self.sock = ssl.wrap_socket(self.sock, ssl_version=ssl.PROTOCOL_SSLv23)
        self.connection = self.construct_connection(str(self.ip), self.sock)
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
                
    def start_client_runtime(self):
        input_thread = threading.Thread(target=self.command_line_input)
        input_thread.start()
        self.connect_to_server(self.ip, self.port)
    

class AdminClient(BaseClient):
    def submit_password(self, password):
        auth_message = self.construct_authentication_body(self.my_ip, self.ip, password)
        self.client_send(auth_message)


if __name__ == "__main__":
    client = BaseClient()

    def command_line_input(self):
        while True:
            try:
                command = input("\n> ")
                message = self.construct_base_body(self.ip, command)
                self.client_send_all(message)
            except (EOFError, KeyboardInterrupt):
                self.sel.unregister(self.connection.conn)
                self.connection.conn.close()
                os._exit(0)
    client.start_client_runtime()