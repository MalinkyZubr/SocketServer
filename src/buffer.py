import socket
import json
import sys
import time
import pydantic
import typing
import datetime
from typing import Any
from schemas import BaseSchema


class buffer:
    buffer_size = 4096
    server_buffer = False
    origin_ip = ''
    
    @staticmethod
    def set_origin_ip(origin_ip: str):
        buffer.origin_ip = origin_ip

    @staticmethod
    def set_buffer_server(t:bool):
        buffer.server_buffer = t
        
    @staticmethod
    def set_buffer_size(buffer_size):
        buffer.buffer_size = buffer_size

    @staticmethod
    def get_buffer_size():
        return buffer.buffer_size
    
    @staticmethod
    def unpack_data(data):
        return json.loads(data.decode('utf-8'))

    @staticmethod
    def pack_data(data):
        return json.dumps(data).encode('utf-8')

    @staticmethod
    def data_length(data):
        num_fragments = int((len(data) / buffer.buffer_size) + 1)
        return num_fragments

    @staticmethod
    def prepare_all(data: str | list | dict | int | float, destination_ip: str, package=BaseSchema()):
        package.origin_ip = buffer.origin_ip
        package.request_body = data
        package.time = str(datetime.datetime.now().strftime("%H:%M:%S"))

        package = package.dict()

        encoded_data = buffer.pack_data(package)
        fragments = buffer.data_length(encoded_data)
        encoded_data_fragments = []
        for x in range(fragments):
            data_index = x * buffer.buffer_size
            if data_index + 4096 > len(encoded_data):
                encoded_data_fragments.append(encoded_data[data_index:])
            else:
                encoded_data_fragments.append(encoded_data[data_index:data_index + buffer.buffer_size])
                
        if len(encoded_data_fragments[-1]) == buffer.buffer_size:
            encoded_data_fragments.append(buffer.pack_data("end"))

        return encoded_data_fragments

    @staticmethod
    def send_all(data, connection, destination='127.0.0.1'):
        if buffer.server_buffer:
            for fragment in data:
                connection.conn.send(fragment)
        else:
            for fragment in buffer.prepare_all(data, destination):
                connection.send(fragment)

    @staticmethod
    def recv_all(connection: BaseSchema):
        aggregate_data = []
        length = 4096
        while length == 4096:
            loop_data = connection.recv(buffer.buffer_size)
            length = len(loop_data)
            aggregate_data.append(loop_data)
        
        if buffer.server_buffer:
            return aggregate_data, b"".join(aggregate_data)
        return b"".join(aggregate_data)


# if __name__ == "__main__":
#     with open(r"C:\Users\ahuma\Desktop\Programming\Networking\SocketServer\tests\test_file.txt", 'r') as f:
#         data = f.read()
#     buffer.prepare_all(data, '1', '2')
