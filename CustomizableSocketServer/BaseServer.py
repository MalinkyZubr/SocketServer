import selectors
import socket
import json
import logging
import ssl
import getpass
import hashlib
from typing import Type, Optional, Callable
if __name__ != "__main__":
    from . import SocketOperations as so
    from . import exceptions as exc
    from . import schemas
else:
    import SocketOperations as so
    import exceptions as exc
    import schemas
logging.basicConfig(level=logging.INFO)


class BaseServer(so.BaseSocketOperator):
    """
    Base server class.
    """
    def __init__(self, cert_dir: str, key_dir: str, external_commands: dict={}, ip: str=so.LOCALHOST, port: int=8000, buffer_size: int=4096, log_dir: Optional[str]=None):
        self.create_logger(log_dir=log_dir)
        self.set_type_server()
        self.set_buffer_size(buffer_size)
        self.connections = []
        self.ip: str = ip
        self.port: int = port
        self.set_my_ip(ip)
        self.hostname: str = socket.gethostbyaddr(ip)
        self.sel = selectors.DefaultSelector()

        self.password = ""

        self.commands = {"get_clients":self.__get_clients, 'shutdown':self.__shutdown}.update(external_commands)

        self.cert_dir = cert_dir
        self.key_dir = key_dir

        # Socket Setup
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setblocking(False)
        self.sock.bind((ip, port))
        self.sock.listen(10)

    def __get_clients(self, **kwargs: dict) -> list:
        return [conn.__str__() for conn in self.connections]

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
            self.send_all(shutdown_message, connection)

    def __process_command(self, command_body: schemas.CommandBody) -> tuple[str, dict]:
        command = command_body.command
        kwargs = command_body.kwargs
        return command, kwargs

    def __command_executor(self, source_connection: so.ServerSideConnection, request_body: schemas.BaseBody) -> schemas.BaseBody:
        command, kwargs = self.__process_command(request_body)
        kwargs['admin'] = source_connection.admin
        result = self.commands.get(command)(**kwargs)
        send_data = self.construct_base_body(connection=source_connection, content=result)
        return send_data

    def __server_send_all(self, data: Type[schemas.BaseSchema]):
        connection = self.__find_connection(data.destination_ip)
        data = self.prepare_all(data)
        for fragment in data: 
            connection.conn.send(fragment)

    def __process_requests(self, source_connection: so.ServerSideConnection) -> None:
        try:
            agg_data: schemas.BaseSchema = self.recv_all(source_connection)
            message_type: str = agg_data.message_type
            request_body: Type[schemas.BaseBody] = agg_data.request_body

            if message_type == "command": # if the command is designated for the server
                send_data: schemas.BaseBody = self.__command_executor(source_connection, request_body)

            elif message_type == "authentication":
                password: str = request_body.password
                send_data: schemas.BaseBody = self.__verify_credential(password, source_connection)

            send_data = agg_data
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
            self.logger.info(f'Connection request with {addr[0]} received')
            conn = ssl.wrap_socket(conn, ssl_version=ssl.PROTOCOL_SSLv23, server_side=True, certfile=self.cert_dir, keyfile=self.key_dir)
            conn.setblocking(False)
            connection = self.construct_connection(str(addr[0]), conn)
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
                password = getpass.getpass(prompt="Enter the server password: ")
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