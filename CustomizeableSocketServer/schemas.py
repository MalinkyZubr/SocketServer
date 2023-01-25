import selectors
import socket
import json
from typing import Optional, Union, IO, Type
from pydantic import BaseModel
import logging
import time


class BaseBody(BaseModel):
    content: str | dict | list = ""


class FileBody(BaseBody):
    file_type: str
    target_path: str
    file_content: bytes


class CommandBody(BaseBody):
    command: str
    kwargs: dict


class BaseSchema(BaseModel):
    origin_ip: str
    destination_ip: str 
    time: str
    request_body: Type[BaseBody]
