from typing import Type, Any
from pydantic import BaseModel


class BaseBody(BaseModel):
    content: str | dict | list = ""


class FileBody(BaseBody):
    file_name: str
    target_path: str | None
    file_content: bytes


class CommandBody(BaseBody):
    command: dict | list
    kwargs: dict


class AuthenticationBody(BaseBody):
    password: str


class BaseSchema(BaseModel):
    origin_ip: str
    destination_ip: str 
    message_type: str
    time: str
    request_body: Any  

