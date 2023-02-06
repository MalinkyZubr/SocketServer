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
        self.__received = []
        self.__server_connection = None
        self.__client_client_connections: list[so.ClientSideConnection]
        my_hostname = socket.gethostname()
        self.set_my_ip(socket.gethostbyname(my_hostname))
        
        self.ip = ip
        self.port = port
        self.sock: IO = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sel = selectors.DefaultSelector()

    def __check_connection_table(self, message: Type[schemas.BaseSchema]):
        origin_connection = self.construct_connection(message.ip)
        if origin_connection not in self.__client_client_connections:
            self.__client_client_connections.append(origin_connection)

    def __receive_messages(self):
        agg_data = self.recv_all(self.__server_connection)
        self.__received.append(agg_data)
        self.__check_connection_table(agg_data)
        
    def client_send_all(self, data: Type[schemas.BaseSchema]):
        """
        send a request to the established socket connection
        """
        data = self.prepare_all(data)
        for fragment in data: 
            self.__server_connection.conn.send(fragment)

    def connect_to_server(self):
        """
        connect to the server and establish a selector to handle operations
        """
        try:
            self.sock.connect((self.ip, self.port))
            self.sock = ssl.wrap_socket(self.sock, ssl_version=ssl.PROTOCOL_SSLv23)
            self.__server_connection = self.construct_connection(str(self.ip), self.sock)
            self.sel.register(self.__server_connection.conn, selectors.EVENT_READ, self.__receive_messages)
        except Exception as e:
            self.logger.error(str(e))
        while True:
            events = self.sel.select()
            for key, mask in events:
                callback = key.data
                callback()

    def get_server_connection(self) -> so.ClientSideConnection:
        """
        return the connection to the server
        """
        return self.__server_connection
    
    def get_received(self) -> list[Type[schemas.BaseSchema]]:
        """
        return the list of messages received
        """
        return self.received
        
    def get_first_in_received(self) -> Type[schemas.BaseSchema]:
        """
        interprets the received messages list as a queue, and returns the first message in the list, before popping it from the list
        """
        try:
            first_in_queue = self.received[0]
            self.received.pop(0)
            return first_in_queue
        except IndexError:
            return None
    

class AdminClient(BaseClient):
    def submit_password(self, password: str):
        auth_message = self.construct_authentication_body(password)
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