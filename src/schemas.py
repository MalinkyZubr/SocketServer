import selectors
import socket
import json
from typing import Optional, Union
from pydantic import BaseModel
import logging
import time


class BaseSchema(BaseModel):
    origin_ip: str = '127.0.0.1'
    t: str = 'standard'
    destination_ip: str = '127.0.0.1'
    time: str="NA"
    request_body: str | list | dict | int | float=""

class PingSchema(BaseModel):
    destination_ip: str = '127.0.0.1'
    t: str = 'ping'


