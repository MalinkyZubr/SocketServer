import selectors
import socket
import json
from typing import Optional, Union
from pydantic import BaseModel
import logging
import time


class BaseSchema(BaseModel):
    origin_ip: str
    destination_ip: str 
    t: str = 'standard'
    time: str
    request_body: str | list | dict | int | float

class PingSchema(BaseModel):
    destination_ip: str
    t: str = 'ping'


