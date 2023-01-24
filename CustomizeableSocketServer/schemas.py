import selectors
import socket
import json
from typing import Optional, Union, IO
from pydantic import BaseModel
import logging
import time


class BaseSchema(BaseModel):
    origin_ip: str
    destination_ip: str 
    message_type: str = 'to_client'
    time: str
    request_body: str | list | dict | int | float


