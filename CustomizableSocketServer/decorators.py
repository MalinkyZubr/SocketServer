import typing
import socket
import sys
import time
import functools
from functools import update_wrapper, partial


class BaseRequirementDecorator():
    """
    class RequiresAuthentication(BaseRequirementDecorator):
        def __call__(self, obj, *args, **kwargs):
            pass
    """
    connection: typing.Optional[socket.socket] = None
    username: typing.Optional[str] = None
    password: typing.Optional[str] = None
    def __init__(self, func: typing.Callable):
        update_wrapper(self, func)
        self.function = func
        self.__code__ = func.__code__
        self.__doc__ = func.__doc__
        self.__name__ = func.__name__
    
    def __get__(self, obj, objtype): 
        """Support instance methods."""
        part = partial(self.__call__, obj)
        part.__code__ = self.__code__
        part.__doc__ = self.__doc__
        part.__name__ = self.__name__
        return part
    
    def __repr__(self):
        return str(self.function)
    
    def __str__(self):
        return str(self.function)
        
    
class DecoratorSetup:
    def configure_decorators(self):
        BaseRequirementDecorator.connection = self.connection
        BaseRequirementDecorator.username = self.username
        BaseRequirementDecorator.password = self.password