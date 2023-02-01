import json
import datetime
from typing import Type, Any
from schemas import BaseSchema
import base64 as b64
from pydantic import BaseModel
from schemas import BaseBody, BaseSchema, AuthenticationBody, CommandBody, FileBody
import schemas


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


class BaseSocketOperator(ConnectionConstructor, FileHandler):
    __my_ip: str = ""
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
        num_fragments = int(len(data) / self.__buffer_size) + 1# what about the edgecase where the data size is a multiple of the self size?
        return num_fragments

    def __prepare_all(self, package: Type[BaseSchema]) -> list:
        package = package.dict()

        encoded_data = self.__pack_data(package)
        fragments = self.__calculate_data_length(encoded_data)
        encoded_data_fragments = []
        for x in range(fragments):
            data_index = x * self.__buffer_size
            if (data_index + self.__buffer_size) > len(encoded_data):
                encoded_data_fragments.append(encoded_data[data_index:])
            else:
                encoded_data_fragments.append(encoded_data[data_index:data_index + self.__buffer_size])
        
        if len(encoded_data_fragments) > 1:
            if len(encoded_data_fragments[-1]) == self.__buffer_size:
                encoded_data_fragments.append(self.__pack_data("end"))

        return encoded_data_fragments

    def send_all(self, data: Type[BaseSchema], connection: Type[ClientSideConnection]):
        data = self.__prepare_all(data)
        for fragment in data: 
            connection.conn.send(fragment)

    def recv_all(self, connection: Type[ClientSideConnection]) -> tuple[list, Any]:
        aggregate_data = []
        length = self.__buffer_size
        while length == self.__buffer_size:
            loop_data = connection.conn.recv(self.__buffer_size)
            if loop_data == 'end': # in case the message is an exact multiple of the buffer size
                break
            length = len(loop_data)
            aggregate_data.append(loop_data)
        
        return self.__unpack_data(b"".join(aggregate_data))

    def set_my_ip(self, my_ip):
        BaseSocketOperator.__my_ip = my_ip

    def my_ip(self):
        return BaseSocketOperator.__my_ip

    def __construct_message(self, destination_ip: str, request_body: Type[BaseBody], message_type: str) -> Type[BaseSchema]:
        schema = BaseSchema(origin_ip=self.my_ip(), 
                            destination_ip=destination_ip, 
                            request_body=request_body, 
                            message_type=message_type,
                            time=str(datetime.datetime.now().strftime("%H:%M:%S")))
        return schema

    def construct_base_body(self, destination_ip: str, content: dict | list | str) -> list:
        body = BaseBody(content=content)
        message = self.__construct_message(destination_ip, body, "standard")
        return message

    def construct_file_body(self, destination_ip: str, file_type: str, source_path: str, target_path: str, content: str="") -> list:
        file_content = self.__upload_file(source_path)
        body = FileBody(file_type=file_type, 
                        target_path=target_path,
                        file_content=file_content,
                        content=content)
        message = self.__construct_message(destination_ip, body, "file")
        return message

    def construct_command_body(self, destination_ip: str, command: str, **kwargs: str) -> list:
        body = CommandBody(command=command,
                           kwargs=kwargs)
        message = self.__construct_message(destination_ip, body, "command")
        return message

    def construct_authentication_body(self, destination_ip: str, password: str) -> list:
        body = AuthenticationBody(password=password)
        message = self.__construct_message(destination_ip, body, "authentication")
        return message


    