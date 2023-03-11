import json
import datetime
from typing import Type, Any, Optional, Callable
import base64 as b64
from pydantic import BaseModel
import logging
import socket
import ssl
import subprocess
import argparse
import typing
from TypeEnforcement import type_enforcer as t
try:
    from . import schemas
    from . import exceptions as exc
except:
    import schemas
    import exceptions as exc


DEFAULT_ROUTE: str = "0.0.0.0"
LOCALHOST: str = "127.0.0.1"

NO_EXECUTOR: int = 0
LEVEL_1_EXECUTOR: int = 1
LEVEL_2_EXECUTOR: int = 2

enforcer = t.TypeEnforcer.enforcer

class SocketObject:
    """
    Stand in class for the socket.socket object. THIS IS ONLY USED FOR TYPE HINTS
    """
    pass



class StandardConnection(BaseModel):
    hostname: str
    ip: str
    conn: Any


class ServerSideConnection(StandardConnection):
    admin: bool = False


class FileHandler:
    def upload_file(self, file_path: str) -> bytes:
        with open(file_path, 'rb') as f:
            return b64.b64encode(f.read()).decode('utf-8')

    def download_file(self, file: Type[schemas.FileBody]):
        if file.target_path:
            with open(file.target_path + file.name, 'wb') as f:
                f.write(b64.b64decode(file.filecontent))
                return 
        with open(".", 'wb') as f:
                f.write(b64.b64decode(file.filecontent))


class Logger:
    @enforcer(recursive=True)
    def create_logger(self, background: int=0, log_dir: str | None=None):
        """
        creates the logger object
        """
        if not background:
            self.logger = logging.getLogger(__name__)
            if log_dir:
                f_handler = logging.FileHandler(log_dir)
                f_handler.setLevel(logging.INFO)

                f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
                f_handler.setFormatter(f_format)

                self.logger.addHandler(f_handler)


class Command:
    @enforcer
    def __init__(self, name: str, command: Callable):
        self.name = name
        self.command = command
        self.hints = self.__generate_hints_dict(command)
        self.help_menu = self.__generate_help_menu(self.hints)

    @enforcer
    def __generate_hints_dict(self, func: Callable) -> dict:
        args = func.__code__.co_varnames
        incomplete_hints = typing.get_type_hints(func)

        if 'return' in incomplete_hints:
            incomplete_hints.pop('return')

        complete_hints: dict = dict()
        
        for arg_name in args:
            try:
                complete_hints.update({arg_name:incomplete_hints[arg_name]})
            except KeyError:
                complete_hints.update({arg_name:typing.Any})
        
        return complete_hints
    
    @enforcer(recursive=True)
    def __generate_help_menu(self, args: dict) -> str:
        func_help = f"Command {self.command}:\n"
        for arg, dtype in args.items():
            func_help += f"\t--{arg} expects a(n) {dtype}\n"


class BaseSocketOperator(FileHandler, Logger):
    @enforcer(recursive=True)
    def __init__(self, port: int, buffer_size: int, executor: int=NO_EXECUTOR, cert_path: str | None=None, key_path: str | None=None):
        self.commands = dict() # update this so it iterates to create command things, the argparse
        self.port = port
        self.my_hostname = socket.gethostname()
        self.my_ip = socket.gethostbyname(self.my_hostname)
        self.executor = executor
        self.cert_path = cert_path
        self.key_path = key_path

        self.parser = argparse.ArgumentParser(prog=__name__)
        try:
            self.__set_buffer_size(buffer_size)
        except exc.ImproperBufferSize as e:
            print(e + "\n\nBuffersize defaulting to 4096")
            self.__set_buffer_size(4096)

    @enforcer(recursive=True)
    def ssl_wrap(self, connection, address: str):
        if self.type_set == 'server':
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.load_cert_chain(self.cert_path, self.key_path)
            wrapped = context.wrap_socket(connection, server_side=True)
        else:
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            context.load_verify_locations(self.cert_path)
            wrapped = context.wrap_socket(connection, server_hostname=socket.gethostbyaddr(address)[0])
        return wrapped

    @enforcer(recursive=True)
    def __set_buffer_size(self, buffer_size: int):
        """
        set the size of the buffer
        """
        if (buffer_size & buffer_size-1)==0:
            self.buffer_size = buffer_size
        else:
            raise exc.ImproperBufferSize() 
    
    @enforcer(recursive=True)
    def __unpack_data(self, data: bytes) -> dict | list | str:
        return json.loads(b64.b64decode(data).decode())

    @enforcer(recursive=True)
    def __pack_data(self, data: dict | list | str) -> bytes:
        return b64.b64encode(json.dumps(data).encode())

    @enforcer(recursive=True)
    def __calculate_data_length(self, data: bytes) -> int:
        num_fragments = int(len(data) / self.buffer_size) + 1# what about the edgecase where the data size is a multiple of the self size?
        return num_fragments

    @enforcer(recursive=True)
    def prepare_all(self, package: Type[schemas.BaseSchema]) -> list:
        """
        take a message and encode it, then break it into its constituent parts in preparation to be send over a socket connection. 
        Only use if you want to create your own custom sending methods for the client or server. Otherwise, this is already built in
        """
        package = package.dict()

        encoded_data = self.__pack_data(package)
        fragments = self.__calculate_data_length(encoded_data)
        encoded_data_fragments = []
        for x in range(fragments):
            data_index = x * self.buffer_size
            if (data_index + self.buffer_size) > len(encoded_data):
                encoded_data_fragments.append(encoded_data[data_index:])
            else:
                encoded_data_fragments.append(encoded_data[data_index:data_index + self.buffer_size])
        
        if len(encoded_data_fragments) > 1:
            if len(encoded_data_fragments[-1]) == self.buffer_size:
                encoded_data_fragments.append(self.__pack_data("end"))

        return encoded_data_fragments

    @enforcer(recursive=True)
    def recv_all(self, connection: Type[StandardConnection]) -> tuple[list, Any]:
        """
        receive all incoming message fragments, re-assemble, and decode them to get the Schema object back.
        """
        aggregate_data = []
        length = self.buffer_size
        while length == self.buffer_size:
            loop_data = connection.conn.recv(self.buffer_size)
            if self.__unpack_data(loop_data) == 'end': # in case the message is an exact multiple of the buffer size
                break
            length = len(loop_data)
            aggregate_data.append(loop_data)
        
        return schemas.BaseSchema(**self.__unpack_data(b"".join(aggregate_data)))

    def set_type_server(self):
        """
        set the socket type to server. Only used once during instantiation to configure socket operations.
        """
        self.type_set = "server"

    def set_type_client(self):
        """
        set the socket type to client. Only used once during instantiation to configure socket operations.
        """
        self.type_set = "client"

    @enforcer(recursive=True)
    def add_command(self, command: dict[str, Callable]):
        """
        accepts a command to add to the object command list. Must be in the format {"command_name":function}
        """
        name, command = list(command.items())[0]
        if name in self.commands:
            raise exc.CommandAlreadyExists()
        command = Command(name, command)
        for varname in command.hints:
            if varname not in list(vars(self.parser.parse_args()).keys()):
                self.parser.add_argument(f"--{varname}")
        self.commands.update({name:command})

    @enforcer(recursive=True)
    def command_executor(self, request: Type[schemas.BaseSchema], source_connection: Type[StandardConnection]) -> schemas.BaseSchema:
        command = request.request_body['command'].split(' ')
        command_name = command[0]
        if (command_name in self.commands and self.executor < LEVEL_1_EXECUTOR) or (command_name not in self.commands and self.executor < LEVEL_2_EXECUTOR):
            raise exc.CommandExecutionNotAllowed
        elif command_name in self.commands and self.executor >= LEVEL_1_EXECUTOR:
            try:
                command = vars(self.parser.parse_args(command[1:]))
                results = self.commands[command_name].command(**command)
            except TypeError:
                raise exc.CommandExecutionError(self.commands[command_name].help_menu)
        elif command_name not in self.commands and self.executor == LEVEL_1_EXECUTOR:
            raise exc.CommandNotFound
        elif command_name not in self.commands and self.executor >= LEVEL_2_EXECUTOR:
            results = subprocess.check_output(command)
        return results

    @enforcer(recursive=True)
    def __construct_message(self, connection: Type[StandardConnection] | str, request_body: Type[schemas.BaseBody], message_type: str) -> Type[schemas.BaseSchema]:
        try:
            ip = connection.ip
        except:
            ip = connection
        schema = schemas.BaseSchema(origin_ip=self.my_ip, 
                            destination_ip=ip, 
                            request_body=request_body, 
                            message_type=message_type,
                            time=str(datetime.datetime.now().strftime("%H:%M:%S")))
        return schema

    @enforcer(recursive=True)
    def construct_base_body(self, connection: Type[StandardConnection] | str, content: dict | list | str) -> schemas.BaseBody:
        """
        construct a standard message to be forwarded to another client via the server
        """
        body = schemas.BaseBody(content=content)
        message = self.__construct_message(connection, body, "standard")
        return message

    @enforcer(recursive=True)
    def construct_file_body(self, connection: Type[StandardConnection] | str, source_path: str, target_path: str | None) -> schemas.FileBody:
        """
        construct a file transfer message to be forwarded to another client via the server
        """
        file_name = source_path.split(r"\\")[-1]
        file_content = self.upload_file(source_path)
        body = schemas.FileBody(file_name=file_name, 
                        target_path=target_path,
                        file_content=file_content)
        message = self.__construct_message(connection, body, "file")
        return message

    @enforcer(recursive=True)
    def construct_command_body(self, command: str, connection: Type[StandardConnection] | str | None=None) -> schemas.CommandBody:
        """
        construct a command message to be issued directly to the server. The desired command must exist within
        the server's command dictionary, as is, or as added by the user
        set connection to None if you only want to send command to the server.
        """
        command = command.split(' ')
        if not connection:
            connection = 'server'
        body = schemas.CommandBody(command=command)
        message = self.__construct_message(connection, body, "command")
        return message

    @enforcer(recursive=True)
    def construct_authentication_body(self, connection: Type[StandardConnection] | str | None, password: str) -> schemas.AuthenticationBody:
        """
        construct an authentication body to submit password to gain admin permissions on the server
        set connection to None if you want to send the authentication to only the server
        """
        if not connection:
            connection = 'server'
        body = schemas.AuthenticationBody(password=password)
        message = self.__construct_message(connection, body, "authentication")
        return message

    @enforcer(recursive=True)
    def construct_connection(self, ip: str, conn: Any=None) -> Type[StandardConnection]:
        """
        create a connection object to be used for connection operations
        """
        if self.type_set == "client":
            connection = StandardConnection(hostname=str(socket.gethostbyaddr(ip))[0], ip=ip, conn=conn)
        else: 
            connection = ServerSideConnection(hostname=str(socket.gethostbyaddr(ip))[0], ip=ip, conn=conn)
        return connection