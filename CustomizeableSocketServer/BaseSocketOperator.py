import socket
import json
import datetime
from typing import Type, IO
from schemas import BaseSchema


class Connection:
    def __init__(self, ip: str, conn: IO, hostname: str):
        self.ip = ip
        self.conn = conn
        self.hostname = hostname

    def __str__(self):
        return f"""
        IP: {self.ip}
        HOSTNAME: {self.hostname}
        CONN: {self.conn}
                """


class BaseSocketOperator:
    def __init__(self):
        self.__buffer_size = 4096

    def set_buffer_size(self, __buffer_size):
        self.__buffer_size = __buffer_size

    def get_buffer_size(self):
        return self.__buffer_size
    
    def unpack_data(self, data):
        return json.loads(data.decode('utf-8'))

    def pack_data(self, data):
        return json.dumps(data).encode('utf-8')

    def construct_message(self, origin_ip: str, destination_ip: str, message_type: str, request_body: str | list | dict | int | float) -> Type[BaseSchema]:
        message = BaseSchema()
        message.origin_ip = origin_ip
        message.destination_ip = destination_ip
        message.message_type = message_type
        message.request_body = request_body
        return message

    def calculate_data_length(self, data):
        num_fragments = int(len(data) / self.__buffer_size) # what about the edgecase where the data size is a multiple of the self size?
        return num_fragments

    def prepare_all(self, package: Type[BaseSchema]):
        package.time = str(datetime.datetime.now().strftime("%H:%M:%S"))

        package = package.dict()

        encoded_data = self.pack_data(package)
        fragments = self.calculate_data_length(encoded_data)
        encoded_data_fragments = []
        for x in range(fragments):
            data_index = x * self.__buffer_size
            if data_index + 4096 > len(encoded_data):
                encoded_data_fragments.append(encoded_data[data_index:])
            else:
                encoded_data_fragments.append(encoded_data[data_index:data_index + self.__buffer_size])
                
        if len(encoded_data_fragments[-1]) == self.__buffer_size:
            encoded_data_fragments.append(self.pack_data("end"))

        return encoded_data_fragments

    def send_all(self, data, connection: Connection):
        for fragment in data: 
            connection.conn.send(fragment)

    def recv_all(self, connection: Connection):
        aggregate_data = []
        length = self.__buffer_size
        while length == self.__buffer_size:
            loop_data = connection.conn.recv(self.__buffer_size)
            length = len(loop_data)
            aggregate_data.append(loop_data)
        
        return aggregate_data, self.unpack_data(b"".join(aggregate_data))
