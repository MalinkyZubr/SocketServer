import json
import datetime
from typing import Type, IO, Any
from schemas import BaseSchema
import base64 as b64
from pydantic import BaseModel
from schemas import BaseBody, BaseSchema, AuthenticationBody, CommandBody, FileBody
from exceptions import PasswordLengthException


DEFAULT_ROUTE: str = "0.0.0.0"
LOCALHOST: str = "127.0.0.1"

TYPE_CLIENT = "client"
TYPE_SERVER = "server"


class ClientSideConnection(BaseModel):
    hostname: str
    ip: str
    conn: Any


class ServerSideConnection(ClientSideConnection):
    admin: bool = False


class ConnectionConstructor:
    def construct_connection(self, hostname: str, ip: str, conn: Any, type_set: str=TYPE_CLIENT) -> Type[ClientSideConnection]:
        if type_set == TYPE_CLIENT:
            connection = ClientSideConnection(hostname=hostname, ip=ip, conn=conn, type_set=type_set)
        else: 
            connection = ServerSideConnection(hostname=hostname, ip=ip, conn=conn, type_set=type_set)
        return connection


class FileHandler:
    def __upload_file(self, file_path: str) -> bytes:
        with open(file_path, 'rb') as f:
            return b64.b64encode(f.read()).decode('utf-8')

    def __download_file(self, data: bytes, file_path: str):
        with open(file_path, 'wb') as f:
            f.write(b64.b64decode(data))


class SchemaProducer(FileHandler):
    def __construct_message(self, origin_ip: str, destination_ip: str, request_body: Type[BaseBody], message_type: str, schema: Type[BaseSchema]) -> Type[BaseSchema]:
        schema = schema()
        schema.origin_ip = origin_ip
        schema.destination_ip = destination_ip
        schema.request_body = request_body
        schema.message_type = message_type
        return schema

    def construct_base_body(self, origin_ip: str, destination_ip: str, content: dict | list | str) -> list:
        body = BaseBody()
        body.content = content
        message = self.__construct_message(origin_ip, destination_ip, body, "standard")
        return self.__prepare_all(message)

    def construct_file_body(self, origin_ip: str, destination_ip: str, file_type: str, source_path: str, target_path: str, content: str="") -> list:
        file_content = self.__upload_file(source_path)
        body = FileBody()
        body.file_type = file_type
        body.target_path = target_path
        body.file_content = file_content
        body.content = content
        message = self.__construct_message(origin_ip, destination_ip, body, "file")
        return self.__prepare_all(message)

    def construct_command_body(self, origin_ip: str, destination_ip: str, command: str, **kwargs: str) -> list:
        body = CommandBody()
        body.command = command
        body.kwargs = kwargs
        message = self.__construct_message(origin_ip, destination_ip, body, "command")
        return self.__prepare_all(message)

    def construct_authentication_body(self, origin_ip: str, destination_ip: str, password: str) -> list:
        body = AuthenticationBody()
        body.password = password
        message = self.__construct_message(origin_ip, destination_ip, body, "authentication")
        return self.__prepare_all(message)


class BaseSocketOperator(SchemaProducer, ConnectionConstructor):
    def __init__(self):
        self.__buffer_size = 4096

    def set_buffer_size(self, __buffer_size):
        self.__buffer_size = __buffer_size

    def get_buffer_size(self) -> int:
        return self.__buffer_size
    
    def __unpack_data(self, data: bytes) -> dict | list | str:
        return json.loads(data.decode())

    def __pack_data(self, data: dict | list | str) -> bytes:
        return json.dumps(data).encode()

    def __calculate_data_length(self, data: bytes) -> int:
        num_fragments = int(len(data) / self.__buffer_size) # what about the edgecase where the data size is a multiple of the self size?
        return num_fragments

    def __prepare_all(self, package: Type[BaseSchema]) -> list:
        package.time = str(datetime.datetime.now().strftime("%H:%M:%S"))

        package = package.dict()

        encoded_data = self.__pack_data(package)
        fragments = self.__calculate_data_length(encoded_data)
        encoded_data_fragments = []
        for x in range(fragments):
            data_index = x * self.__buffer_size
            if data_index + 4096 > len(encoded_data):
                encoded_data_fragments.append(encoded_data[data_index:])
            else:
                encoded_data_fragments.append(encoded_data[data_index:data_index + self.__buffer_size])
                
        if len(encoded_data_fragments[-1]) == self.__buffer_size:
            encoded_data_fragments.append(self.__pack_data("end"))

        return encoded_data_fragments

    def send_all(self, data: list, connection: Type[ClientSideConnection]):
        for fragment in data: 
            connection.conn.send(fragment)

    def recv_all(self, connection: Type[ClientSideConnection]) -> tuple[list, Any]:
        aggregate_data = []
        length = self.__buffer_size
        while length == self.__buffer_size:
            loop_data = connection.conn.recv(self.__buffer_size)
            length = len(loop_data)
            aggregate_data.append(loop_data)

        if self.__unpack_data(aggregate_data[-1]) == 'end': # in case the message is an exact multiple of the buffer size
            aggregate_data = aggregate_data[:-1]
        
        return aggregate_data, self.__unpack_data(b"".join(aggregate_data))