from typing import Type


types = [int, float, bool]

class baseClass():
    x = 0

class subClass(baseClass):
    y = 1


def test(x: Type[baseClass]):
    return None

test(subClass())

class X_CLASS:
    def __str__():
        return "0.0.0.0"

def test2(x: str):
    print(x)

test2(X_CLASS)

