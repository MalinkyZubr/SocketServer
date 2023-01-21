import socket


sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind(('127.0.0.1', 8000))
sock.listen(1)
conn, addr = sock.accept()

print(type(conn))