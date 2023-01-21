import selectors
import socket
import json
from typing import Optional, Union
from pydantic import BaseModel
import logging
import time
import sys
sys.path.insert(0,"..")
from schemas import BaseSchema
from BaseServer import BaseServer


if __name__ == "__main__":
    server = BaseServer(
                        cert_dir=r'C:\Users\ahuma\Desktop\certs\cert.pem',
                        key_dir=r'C:\Users\ahuma\Desktop\certs\private.key'
                       )
    server.start()