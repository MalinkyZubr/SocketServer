# What is this project?
I will be creating a TCP server which can coordinate and maintain connections on several clients. Using selectors

# Some Notes:
1. must generate a private key and cert with openssl to use the server
2. the BaseSocket class is very bare bones, by design. It includes a connection sequence and an echo method, nothing else, so that users can more easily make their own functions
3. The BaseServer class receives messages and forwards them to destination IP addresses connected to the server. The server is functional without any additions (for simple connection handling at least). Instead of giving the server instance direct access to a database, I would recommend creating a client to host it.