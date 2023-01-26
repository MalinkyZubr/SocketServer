import socket
import json
import datetime
from typing import Type, IO, Any
from schemas import BaseSchema, SchemaProducer
import base64 as b64
from pydantic import BaseModel


DEFAULT_ROUTE: str = "0.0.0.0"
LOCALHOST: str = "127.0.0.1"

TYPE_CLIENT = "client"
TYPE_SERVER = "server"


class ClientSideConnection(BaseModel):
    hostname: str
    ip: str
    conn: IO


class ServerSideConnection(ClientSideConnection):
    admin: bool = False


class ConnectionConstructor:
    def construct_connection(self, hostname: str, ip: str, conn: IO, type_set: str=TYPE_CLIENT) -> Type[ClientSideConnection]:
        if type_set == TYPE_CLIENT:
            connection = ClientSideConnection()
        else: 
            connection = ServerSideConnection()
        connection.hostname = hostname
        connection.ip = ip
        connection.conn = conn
        return connection


class FileHandler:
    def __upload_file(self, file_path: str) -> bytes:
        with open(file_path, 'rb') as f:
            return b64.b64encode(f.read()).decode('utf-8')

    def __download_file(self, data: bytes, file_path: str):
        with open(file_path, 'wb') as f:
            f.write(b64.b64decode(data))


class BaseSocketOperator(SchemaProducer, ConnectionConstructor, FileHandler):
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