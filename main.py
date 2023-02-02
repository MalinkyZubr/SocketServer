from CustomizableSocketServer.BaseServer import BaseServer


if __name__ == "__main__":
    server = BaseServer(
        key_dir=r"C:\Users\ahuma\Desktop\certs\key1.pem",
        cert_dir=r"C:\Users\ahuma\Desktop\certs\cert1.pem"
    )
    server.start()