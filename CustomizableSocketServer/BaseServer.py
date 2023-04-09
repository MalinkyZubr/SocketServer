import selectors
import socket
import json
import logging
import sys
import hashlib
import signal
from typing import Type, Optional, Callable
try:
    from . import SocketOperations as so
    from . import exceptions as exc
    from . import schemas
    from . import r_types
except:
    import SocketOperations as so
    import exceptions as exc
    import schemas
    import r_types


class BaseServer(so.BaseSocketOperator):
    """
    Base server class.
    """
    def __init__(self, cert_dir: str, key_dir: str, ip: str=so.LOCALHOST, 
                 port: int=8000, buffer_size: int=4096, log_dir: Optional[str]=None, 
                 request_process: Callable | None=None, acceptance_process: Callable | None = None,
                 password: str | None=None):
        # super init of basesocketoperator here
        super().__init__(port=port, buffer_size=buffer_size, cert_path=cert_dir, key_path=key_dir)

        logging.basicConfig(level=logging.INFO)
        self.create_logger(log_dir=log_dir)
        self.set_type_server()
        self.connections = []
        self.ip: str = ip
        self.sel = selectors.DefaultSelector()
        self.password = ""
        self.acceptance_process = acceptance_process
        self.request_process = request_process
        self.password = password

        signal.signal(signal.SIGINT, self.interrupt_handler)

        # Socket Setup
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setblocking(False)
        self.sock.bind((ip, port))
        self.sock.listen(10)

    def interrupt_handler(self, sig, frame):
        self.shutdown()

    def __find_connection(self, destination_ip: str) -> so.ServerSideConnection:
        for connection in self.connections:
            if connection.ip == destination_ip:
                return connection
        raise exc.ConnectionNotFoundError()

    def get_connections(self):
        return [(connection.hostname, connection.ip) for connection in self.connections]

    def shutdown(self) -> None:
        self.broadcast("Shutting Down Server")
        for connection in self.connections:
            self.sel.unregister(connection.conn)
            connection.conn.close()
        sys.exit()

    def __server_send_all(self, data: Type[schemas.BaseSchema]):
        connection = self.__find_connection(data.destination_ip)
        data = self.prepare_all(data)
        for fragment in data: 
            connection.conn.send(fragment)

    def broadcast(self, data: Type[schemas.BaseSchema]):
        for connection in self.connections:
            message = self.construct_message(connection=connection, request_body=data, message_type=r_types.SERVER_BROADCAST)
            message = self.prepare_all(message)
            for fragment in data: 
                try: connection.conn.send(fragment)
                except: continue

    def __process_requests(self, source_connection: so.ServerSideConnection) -> None:
        try:
            agg_data: schemas.BaseSchema = self.recv_all(source_connection)
            if self.request_process:
                agg_data = self.request_process(agg_data)

            self.__server_send_all(agg_data)

        except json.decoder.JSONDecodeError: # if connection was lost
            self.sel.unregister(source_connection.conn)
            self.connections.remove(source_connection)
            self.logger.error(f"Connection with {source_connection} lost")

        except Exception as error:
            self.logger.error(str(error))
            send_data = self.construct_message(connection=source_connection, content=str(error))
            self.__server_send_all(send_data)

    def __accept_connection(self):
        try:
            conn, addr = self.sock.accept()
            ip = str(addr[0])
            self.logger.info(f'Connection request with ip of {ip} received')
            conn = self.ssl_wrap(conn, ip)
            conn.setblocking(False)
            connection = self.construct_connection(ip, conn)

            if self.acceptance_process:
                self.acceptance_process(connection=connection)

            self.broadcast(f"{connection.hostname} at address {connection.ip} connected to the server")
            self.connections.append(connection)

            self.sel.register(conn, selectors.EVENT_READ, lambda: self.__process_requests(source_connection=connection))
            self.logger.info(f"Connection with {connection} established and stable!")
        except Exception as e:
            self.logger.error(str(e))

    def __hash(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def start(self):
        """
        Starts the server
        """
        self.sel.register(self.sock, selectors.EVENT_READ, self.__accept_connection)
        self.logger.info(f"[+] Starting TCP server on {self.ip}:{self.port}")
        while True:
            events = self.sel.select()
            for key, mask in events:
                callback = key.data
                callback()

    def __str__(self):
        return \
        f"""
        IP: {self.ip}
        PORT: {self.port}
        """


if __name__ == "__main__":
    server = BaseServer(
        ip="192.168.0.161",
        key_dir=r"C:\Users\ahuma\Desktop\programming\Networking\SocketServer\key.pem",
        cert_dir=r"C:\Users\ahuma\Desktop\programming\Networking\SocketServer\cert.pem"
    )
    server.start()