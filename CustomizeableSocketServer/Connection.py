class Connection:
    def __init__(self, ip: str, conn, hostname: str):
        self.ip = ip
        self.conn = conn
        self.hostname = hostname

    def __str__(self):
        return f"""
        IP: {self.ip}
        HOSTNAME: {self.hostname}
        CONN: {self.conn}
                """