import selectors
import socket
from typing import IO, Type
import ssl
import selectors
import logging
import os
import threading
from typing import Optional
if __name__ != "__main__":
    from . import SocketOperations as so
    from . import exceptions as exc
    from . import schemas
else:
    import SocketOperations as so
    import exceptions as exc
    import schemas
logging.basicConfig(level=logging.INFO)


class BaseClient(so.BaseSocketOperator):
    def __init__(self, ip: str=so.LOCALHOST, port: int=8000, buffer_size: int=4096, log_dir: Optional[str]=None):
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
        data = self.prepare_all(data)
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
    

class AdminClient(BaseClient):
    def submit_password(self, password: str):
        auth_message = self.construct_authentication_body(self.ip, password)
        self.client_send(auth_message)


if __name__ == "__main__":
    client = BaseClient()

    def command_line_input():
        while True:
            try:
                command = input("\n> ")
                message = client.construct_base_body(client.connection, command)
                client.client_send_all(message)
            except (EOFError, KeyboardInterrupt) as e:
                print(e)
                client.sel.unregister(client.connection.conn)
                client.connection.conn.close()
                os._exit(0)

    def start_client_runtime():
        input_thread = threading.Thread(target=command_line_input)
        input_thread.start()
        client.connect_to_server()

    start_client_runtime()