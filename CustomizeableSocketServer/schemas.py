import selectors
import socket
import json
from typing import Optional, Union, IO, Type
from pydantic import BaseModel
import logging
import time
from SocketOperations import BaseSocketOperator, FileHandler


class BaseBody(BaseModel):
    content: str | dict | list = ""


class FileBody(BaseBody):
    file_type: str
    target_path: str
    file_content: bytes


class CommandBody(BaseBody):
    command: str
    kwargs: dict


class AuthenticationBody(BaseBody):
    password: str


class BaseSchema(BaseModel):
    origin_ip: str
    destination_ip: str 
    message_type: str
    time: str
    request_body: Type[BaseBody]    


class SchemaProducer(FileHandler):
    def __construct_message(self, origin_ip: str, destination_ip: str, request_body: Type[BaseBody], message_type: str, schema: Type[BaseSchema]=BaseSchema()) -> Type[BaseSchema]:
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