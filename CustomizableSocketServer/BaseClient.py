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
except:
    import SocketOperations as so
    import exceptions as exc
    import schemas
    import utilities


class BaseClient(so.BaseSocketOperator):
    def __init__(self, cert_path: str, standard_rules: list[Callable]=[], 
                 executor: int=so.NO_EXECUTOR, background: bool=False, allowed_file_types: list=[], 
                 server_ip: str=so.LOCALHOST, port: int=8000, buffer_size: int=4096, 
                 log_dir: Optional[str]=None, commands: dict[str:Callable]={}):
        
        logging.basicConfig(level=logging.INFO)
        if isinstance(commands, str) and isinstance(standard_rules, str):
            self.commands, self.standard_rules = utilities.extract_config_pickles(commands, standard_rules)
        super().__init__(commands=commands, port=port, buffer_size=buffer_size, executor=executor, cert_path=cert_path)
        self.create_logger(background=background, log_dir=log_dir)
        self.set_type_client()
        self.__server_connection = None

        self.allowed_file_types = allowed_file_types
        self.background = background
        if not background:
            self.standard_rules = standard_rules + [self.logger.info]
        
        self.server_ip = server_ip
        self.sock: IO = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sel = selectors.DefaultSelector()

    def unpack_config_commands(self, config: dict)->tuple[dict[str:Callable], list[Callable]]:
        self.commands = pickle.loads(bytes(config['commands']))

    def bounceback(self, message: Type[schemas.BaseBody], response: str):
        bounceback = self.construct_base_body(self, message.origin_ip, response)
        self.client_send_all(bounceback)

    def secure_file_download(self, file: Type[schemas.FileBody]):
        if self.allowed_file_types and file.file_type not in self.allowed_file_types:
            decision = str(input(f"The file {file.file_name + file.file_type} is not approved to be automatically downloaded. Do you still want to download it?\n(y/n)"))
            if decision == "y":
                self.download_file(file)
            else:
                raise exc.FileNotApproved

    def filter(self, message: Type[schemas.BaseSchema]):
        message_type = message.message_type
        match message_type:
            case ("standard", self.background):
                self.bounceback(message, f"{self.my_ip} is not accepting standard messages")
            case "standard":
                for operation in self.standard_rules:
                    operation(message)
                return message
            case "file":
                try:
                    self.secure_file_download(message.request_body)
                    self.bounceback(message, "Successful File Download")
                    return "Successful File Download"
                except exc.FileNotApproved:
                    self.bounceback(message, "file type not approved")
                    return "Failed file download"
            case ("command", self.executor):
                try:
                    result = self.command_executor(request=message)
                    self.bounceback(message, result)
                    return result
                except exc.CommandExecutionNotAllowed:
                    self.bounceback(message, "Command execution not allowed on this client")
                except subprocess.CalledProcessError:
                    self.bounceback(message, "Shell failed to execute command")
            case "authentiation":
                self.bounceback("Authentication not allowed")

    def __receive_messages(self):
        agg_data = self.recv_all(self.__server_connection)
        self.filter(agg_data)
        
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
            print(self.sock)
            self.sock = self.ssl_wrap(self.sock, self.server_ip)
            print(self.sock)
            self.__server_connection = self.construct_connection(str(self.server_ip), self.sock)
            self.sel.register(self.__server_connection.conn, selectors.EVENT_READ, self.__receive_messages)
        except Exception as e:
            self.logger.error(str(e))
        while True:
            events = self.sel.select()
            for key, mask in events:
                callback = key.data
                callback()

    def get_server_connection(self) -> so.StandardConnection:
        """
        return the connection to the server
        """
        return self.__server_connection
        
    def get_commands(self):
        message = self.construct_command_body(self.server_ip, "get_commands")
        self.client_send_all(message)
        
    def get_clients(self):
        message = self.construct_command_body(self.server_ip, "get_clients")
        self.client_send_all(message)

    def close_connection(self):
        client.sel.unregister(client.__server_connection.conn)
        client.__server_connection.conn.close()
    

class AdminClient(BaseClient):
    def submit_password(self, password: str):
        auth_message = self.construct_authentication_body(password)
        self.client_send_all(auth_message)

    def shutdown(self):
        message = self.construct_command_body(self.server_ip, "shutdown")
        self.client_send_all(message)


if __name__ == "__main__":
    client = BaseClient(cert_path=r'C:\Users\ahuma\Desktop\certs\cert.pem')

    def command_line_input():
        while True:
            try:
                command = input("\n> ")
                message = client.construct_command_body(connection=None, command=command)
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


class ConfigWrappedClient:
    def __init__(self, client: Type[BaseClient]):
        pass
