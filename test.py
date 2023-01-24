from typing import Type
import base64
import codecs
import json


types = [int, float, bool]

class baseClass():
    x = 0

class subClass(baseClass):
    y = 1


def test(x: Type[baseClass]):
    return None

test(subClass())



def read_file():
    with open(r"C:\Users\ahuma\Desktop\thesecondquestions.pdf", "rb") as f:
        return base64.b64encode(f.read()).decode('utf-8')

def write_file(contents):
    with open(r"C:\Users\ahuma\Desktop\Programming\Networking\SocketServer\test.pdf", 'wb') as f:
        f.write(base64.b64decode(contents))


if __name__ == "__main__":
    code = read_file()
    dumped = json.dumps(code).encode('utf-8')
    print(type(dumped))
    undumped = json.loads(dumped.decode('utf-8'))
    write_file(undumped)


