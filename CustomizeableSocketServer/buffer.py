import socket
import json
import sys
import time
import pydantic
import typing
import datetime
from typing import Type
from schemas import BaseSchema
from Connection import Connection


class buffer:
    __buffer_size = 4096
        
    @staticmethod
    def set_buffer_size(__buffer_size):
        buffer.__buffer_size = __buffer_size

    @staticmethod
    def get_buffer_size():
        return buffer.__buffer_size
    
    @staticmethod
    def unpack_data(data):
        return json.loads(data.decode('utf-8'))

    @staticmethod
    def pack_data(data):
        return json.dumps(data).encode('utf-8')

    @staticmethod
    def data_length(data):
        num_fragments = int(len(data) / buffer.__buffer_size) # what about the edgecase where the data size is a multiple of the buffer size?
        return num_fragments

    @staticmethod
    def prepare_all(package: Type[BaseSchema]):
        package.time = str(datetime.datetime.now().strftime("%H:%M:%S"))

        package = package.dict()

        encoded_data = buffer.pack_data(package)
        fragments = buffer.data_length(encoded_data)
        encoded_data_fragments = []
        for x in range(fragments):
            data_index = x * buffer.__buffer_size
            if data_index + 4096 > len(encoded_data):
                encoded_data_fragments.append(encoded_data[data_index:])
            else:
                encoded_data_fragments.append(encoded_data[data_index:data_index + buffer.__buffer_size])
                
        if len(encoded_data_fragments[-1]) == buffer.__buffer_size:
            encoded_data_fragments.append(buffer.pack_data("end"))

        return encoded_data_fragments

    @staticmethod
    def send_all(data, connection: Connection):
        for fragment in data: #buffer.prepare_all(data, destination):
            connection.conn.send(fragment)

    @staticmethod
    def recv_all(connection: BaseSchema):
        aggregate_data = []
        length = buffer.__buffer_size
        while length == buffer.__buffer_size:
            loop_data = connection.recv(buffer.__buffer_size)
            length = len(loop_data)
            aggregate_data.append(loop_data)
        
        return aggregate_data, buffer.unpack_data(b"".join(aggregate_data))
