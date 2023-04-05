from typing import Type, Any
from pydantic import BaseModel


STANDARD_COMMAND: str = "standard"
CONSOLE_COMMAND: str = "console"


class FileBody(BaseModel):
    file_name: str
    target_path: str | None
    file_content: bytes


class BaseSchema(BaseModel):
    origin_ip: str
    destination_ip: str 
    message_type: str
    time: str
    request_body: Any  

