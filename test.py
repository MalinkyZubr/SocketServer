from typing import Type


types = [int, float, bool]

class baseClass():
    x = 0

class subClass(baseClass):
    y = 1


def test(x: Type[baseClass]):
    return None

test(subClass())