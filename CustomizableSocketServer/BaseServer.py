import selectors
import socket
import json
import logging
import ssl
import getpass
import hashlib
from typing import Type, Optional, Callable
print(__name__)
try:
    from . import SocketOperations as so
    from . import exceptions as exc
    from . import schemas
except:
    import SocketOperations as so
    import exceptions as exc
    import schemas


class BaseServer(so.BaseSocketOperator):
    """
    Base server class.
    """
    def __init__(self, cert_dir: str, key_dir: str, external_commands: dict={}, ip: str=so.LOCALHOST, port: int=8000, buffer_size: int=4096, log_dir: Optional[str]=None):
        # super init of basesocketoperator here
        super().__init__(commands=external_commands, port=port, buffer_size=buffer_size, executor=so.LEVEL_1_EXECUTOR, cert_path=cert_dir, key_path=key_dir)

        logging.basicConfig(level=logging.INFO)
        self.create_logger(log_dir=log_dir)
        self.set_type_server()
        self.connections = []
        self.ip: str = ip
        self.sel = selectors.DefaultSelector()
        self.password = ""

        self.commands.update({"get_clients":self.__get_clients, 'shutdown':self.__shutdown, "get_commands":self.__get_commands})

        # Socket Setup
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setblocking(False)
        self.sock.bind((ip, port))
        self.sock.listen(10)

    def __get_clients(self, **kwargs: dict) -> list:
        return [(conn.hostname, conn.ip) for conn in self.connections]
    
    def __get_commands(self, **kwargs: dict) -> list:
        return list(self.commands.keys())

    def __find_connection(self, destination_ip: str) -> so.ServerSideConnection:
        for connection in self.connections:
            if connection.ip == destination_ip:
                return connection
        raise exc.ConnectionNotFoundError()

    def __check_admin(self, **kwargs: dict) -> None:
        if not kwargs['admin']:
            raise exc.InsufficientPriveleges()

    def __shutdown(self, **kwargs: dict) -> None:
        self.__check_admin(**kwargs)
        for connection in self.connections:
            shutdown_message = self.construct_base_body(self.ip, connection.ip, "Shutting Down Server")
            self.__server_send_all(shutdown_message, connection)

    def __server_send_all(self, data: Type[schemas.BaseSchema]):
        connection = self.__find_connection(data.destination_ip)
        data = self.prepare_all(data)
        for fragment in data: 
            print(type(connection))
            connection.conn.send(fragment)

    def __process_requests(self, source_connection: so.ServerSideConnection) -> None:
        try:
            agg_data: schemas.BaseSchema = self.recv_all(source_connection)
            message_type: str = agg_data.message_type
            request_body: Type[schemas.BaseBody] = agg_data.request_body

            print(f'\n\nAGG DATA: {agg_data}\n\n')

            if message_type == "command" and agg_data.destination_ip == 'server': # if the command is designated for the server
                agg_data.request_body['kwargs']['admin'] = source_connection.admin
                send_data: schemas.BaseSchema = self.command_executor(agg_data)
                print(send_data)
                print("done with this")

            elif message_type == "authentication" and agg_data.destination_ip == self.my_ip:
                password: str = request_body.password
                send_data: schemas.BaseSchema = self.construct_base_body(source_connection, self.__verify_credential(password, source_connection))
            else:
                send_data = agg_data
            print(send_data)
            self.__server_send_all(send_data)

        except json.decoder.JSONDecodeError: # if connection was lost
            self.sel.unregister(source_connection.conn)
            self.connections.remove(source_connection)
            self.logger.error(f"Connection with {source_connection} lost")

        except Exception as error:
            self.logger.error(str(error))
            send_data = self.construct_base_body(connection=source_connection, content=str(error))
            self.__server_send_all(send_data)

    def __accept_connection(self):
        try:
            conn, addr = self.sock.accept()
            ip = str(addr[0])
            self.logger.info(f'Connection request with ip of {ip} received')
            #conn = ssl.wrap_socket(conn, ssl_version=ssl.PROTOCOL_SSLv23, server_side=True, certfile=self.cert_dir, keyfile=self.key_dir)
            conn = self.ssl_wrap(conn, ip)
            conn.setblocking(False)
            connection = self.construct_connection(ip, conn)
            self.connections.append(connection)

            self.sel.register(conn, selectors.EVENT_READ, lambda: self.__process_requests(source_connection=connection))
            self.logger.info(f"Connection with {connection} established and stable!")
        except Exception as e:
            self.logger.error(str(e))

    def __hash(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def __verify_credential(self, password: str, conn: so.ServerSideConnection) -> str:
        if self.__hash(password) == self.password:
            conn.admin = True
            return "Password authentication successful. Priveleges upgraded" 
        raise exc.AuthenticationFailure()

    def __initialize_password(self, password: str | None=None) -> None:
        if not password:
            while True:
                password = "thisisatestpaswordthisisatest" #getpass.getpass(prompt="Enter the server password: ")
                if len(password) < 10:
                    print("\nPassword length is too low, must be at least 10 characters!\n")
                    continue
                break
        elif len(password) < 10:
            raise exc.PasswordLengthException()
                
        self.password = self.__hash(password)

    def add_command(self, command: dict[str, Callable]):
        """
        accepts a command to add to the object command list. Must be in the format {"command_name":function}
        """
        self.commands.update(command)

    def start(self):
        """
        Starts the server
        """
        self.__initialize_password()
        self.sel.register(self.sock, selectors.EVENT_READ, self.__accept_connection)
        self.logger.info(f"[+] Starting TCP server on {self.ip}:{self.port}")
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


if __name__ == "__main__":
    server = BaseServer(
        key_dir=r"C:\Users\ahuma\Desktop\certs\key.pem",
        cert_dir=r"C:\Users\ahuma\Desktop\certs\cert.pem"
    )
    server.start()