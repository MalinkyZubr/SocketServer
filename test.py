class Connection:
    def __init__(self, ip: str, conn, hostname: str):
        self.ip = ip
        self.conn = conn
        self.hostname = hostname

    def __str__(self):
        return f"""IP: {self.ip}
        HOSTNAME: {self.hostname}
        CONN: {self.conn}
                """


x = Connection('x', 'z', 'y')
print(x)

print(x.__str__())

z = {'y':'z'}
print(list(z.keys())[0])


def change_feature(x):
    x.conn = "Hehehe"

change_feature(x)
print(x)