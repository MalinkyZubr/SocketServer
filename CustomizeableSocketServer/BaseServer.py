import selectors
import socket
import json
from typing import Optional, Union
import logging
import time
import sys
import ssl
from SocketOperations import BaseSocketOperator, TYPE_SERVER, ServerSideConnection
from schemas import BaseSchema, BaseBody, FileBody, CommandBody
import SocketOperations
import getpass
import hashlib


class BaseServer(BaseSocketOperator):
    def __init__(self, external_commands: dict={}, ip: str='192.168.0.161', port: int=8000, timeout: int=1000, buffer_size: int=4096, cert_dir=None, key_dir=None):
        self.set_buffer_size(buffer_size)
        self.connections = []
        self.ip: str = ip
        self.port: int = port
        self.hostname: str = socket.gethostbyaddr(ip)
        self.sel = selectors.DefaultSelector()

        self.password = ""

        self.commands = {"get_clients":self.__get_clients, 'shutdown':self.__shutdown} + external_commands

        self.cert_dir = cert_dir
        self.key_dir = key_dir

        # Socket Setup
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(timeout)
        self.sock.setblocking(False)
        self.sock.bind((ip, port))
        self.sock.listen(10)

    def __get_clients(self, **kwargs):
        return [conn.__str__() for conn in self.connections]

    def __find_connection(self, destination_ip: str) -> ServerSideConnection | bool:
        for connection in self.connections:
            if connection.ip == destination_ip:
                return connection
            raise "Connection Not Found"

    def __check_admin(self, **kwargs):
        if not kwargs['admin']:
            raise "Not Authenticated: Need admin to execute this command"

    def __shutdown(self, **kwargs):
        self.__check_admin(**kwargs)
        for connection in self.connections:
            shutdown_message = self.construct_base_body(self.ip, connection.ip, "Shutting Down Server")
            self.send_all(shutdown_message, connection)

    def __process_command(self, command_body: CommandBody) -> tuple[str, dict]:
        command = command_body.get('command')
        kwargs = command_body.get('kwargs')
        return command, kwargs

    def __process_requests(self, source_connection: ServerSideConnection):
        try:
            frag_data, agg_data = self.recv_all(source_connection) 
            destination_ip = agg_data.get('destination_ip')
            message_type = agg_data.get('message_type')
            request_body = agg_data.get('request_body')
            if message_type == "command": # if the command is designated for the server
                forward_destination: ServerSideConnection = source_connection
                command, kwargs = self.__process_command(request_body)
                kwargs['admin'] = source_connection.admin
                result = self.commands.get(command)(**kwargs)
                send_data = self.construct_base_body(self.ip, forward_destination, result)
            elif message_type == "authentication":
                password = request_body.get('password')
                send_data = self.__check_password(password, source_connection)
                forward_destination: ServerSideConnection = source_connection
            else: # if designated for another client
                send_data = frag_data
                forward_destination: ServerSideConnection = self.__find_connection(destination_ip)
        except json.decoder.JSONDecodeError:
            self.sel.unregister(connection.conn)
            self.connections.remove(connection)
            print("connection_failure")
        except Exception as error:
            send_data = self.construct_base_body(self.ip, forward_destination, error)

        self.send_all(send_data, forward_destination)
        
    def accept_connection(self):
        conn, addr = self.sock.accept()
        print("Connection Accepted")
        conn = ssl.wrap_socket(conn, ssl_version=ssl.PROTOCOL_SSLv23, server_side=True, certfile=self.cert_dir, keyfile=self.key_dir)
        conn.setblocking(False)
        connection = self.create_connection(socket.gethostbyaddr(addr[0]), addr[0], conn, type_set=TYPE_SERVER)
        self.connections.append(connection)
        self.sel.register(conn, selectors.EVENT_READ, lambda: self.__process_requests(connection=connection))
        print("Connection Started")

    def __hash(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def __check_password(self, password: str, conn: ServerSideConnection) -> str:
        if self.__hash(password) == self.password:
            conn.admin = True
            return "Password authentication successful. Priveleges upgraded" 
        raise "Password authentication failure, incorrect password"

    def __initialize_password(self):
        while True:
            password = getpass.getpass(prompt="Enter the server password: ")
            if len(password) < 10:
                print("\nPassword length is too low, must be at least 10 characters!\n")
                continue
            self.password = self.__hash(password)

    def start(self):
        self.__initialize_password()
        self.sel.register(self.sock, selectors.EVENT_READ, self.accept_connection)
        print(f"[+] Starting TCP server on {self.ip}:{self.port}")
        while True:
            events = self.sel.select()
            for key, mask in events:
                callback = key.data
                callback()

    def __str__(self):
        return f"""
        IP: {self.ip}
        PORT: {self.port}
        """
