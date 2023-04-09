import selectors
import socket
from typing import IO, Type
import ssl
import logging
import os
import threading
import pickle
import subprocess
from typing import Optional, Callable
try:
    from . import SocketOperations as so
    from . import exceptions as exc
    from . import schemas
    from . import utilities
    from . import KillableThread
except:
    import SocketOperations as so
    import exceptions as exc
    import schemas
    import utilities
    import KillableThread


class BaseClient(so.BaseSocketOperator):
    def __init__(self, message_operation: Callable, cert_path: str, 
                 server_ip: str=so.LOCALHOST, port: int=8000, buffer_size: int=4096, 
                 log_dir: Optional[str]=None):
        
        logging.basicConfig(level=logging.INFO)
        super().__init__(port=port, buffer_size=buffer_size, cert_path=cert_path)
        self.create_logger(log_dir=log_dir)
        self.set_type_client()
        self.__server_connection = None

        self.reception_thread = KillableThread.ExitableThread(target=self.__receive_messages, kwargs={"operation":message_operation})
        self.reception_thread.start()
        
        self.server_ip = server_ip
        self.sock: IO = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sel = selectors.DefaultSelector()

    def __receive_messages(self, operation: Callable=print):
        agg_data = self.recv_all(self.__server_connection)
        operation(agg_data)
        
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
            self.sock.connect((self.server_ip, self.port))
            # self.sock = ssl.wrap_socket(self.sock, ssl_version=ssl.PROTOCOL_SSLv23)
            self.sock = self.ssl_wrap(self.sock, self.server_ip)
            self.__server_connection = self.construct_connection(str(self.server_ip), self.sock)
            self.sel.register(self.__server_connection.conn, selectors.EVENT_READ, self.__receive_messages)
        except Exception as e:
            self.logger.error(str(e))
            os._exit(0)
        while True:
            events = self.sel.select()
            for key, mask in events:
                callback = key.data
                callback()

    def close_connection(self):
        self.sel.unregister(self.__server_connection.conn)
        self.__server_connection.conn.close()
        self.reception_thread.exit()



if __name__ == "__main__":
    client = BaseClient(
        message_operation=print,
        server_ip="192.168.0.161",
        cert_path=r'C:\Users\ahuma\Desktop\programming\Networking\SocketServer\cert.pem'
        )

    def command_line_input():
        while True:
            try:
                command = input("\n> ")
                message = client.construct_message(connection="192.168.0.161", message_type="text", request_body=command)
                client.client_send_all(message)
            except (EOFError, KeyboardInterrupt) as e:
                print(e)
                client.close_connection()
                os._exit(0)
            except Exception as e:
                print(e)

    def start_client_runtime():
        input_thread = threading.Thread(target=command_line_input)
        input_thread.start()
        client.connect_to_server()

    start_client_runtime()

