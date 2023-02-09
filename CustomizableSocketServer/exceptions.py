PASSWORD_LENGTH_EXCEPTION_MESSAGE = "Password length insufficient, 10 characters minimum"
AUTHENTICATION_FAILURE_EXCEPTION_MESSAGE = "Password authentication failure, incorrect password"
CONNECTION_NOT_FOUND_EXCEPTION_MESSAGE = "Connection wasnt found in the connections list"
INSUFFICIENT_PRIVELEGES_MESSAGE = "Not Authenticated: Need admin to execute this command"
BUFFER_EXCEPTION_MESSAGE = "The buffersize must be equal to 2 raised to any power"


class PasswordLengthException(Exception):
    """
    Raise exception when a password is too short
    """
    def __init__(self, message=PASSWORD_LENGTH_EXCEPTION_MESSAGE):
        super().__init__(message)


class AuthenticationFailure(Exception):
    """
    Raise an exception when authentication to the server fails
    """
    def __init__(self, message=AUTHENTICATION_FAILURE_EXCEPTION_MESSAGE):
        super().__init__(message)


class ConnectionNotFoundError(Exception):
    """
    Raise an exception when the server cannot find a connection in its table
    """
    def __init__(self, message=CONNECTION_NOT_FOUND_EXCEPTION_MESSAGE):
        super().__init__(message)


class InsufficientPriveleges(Exception):
    """
    Raise an exception when a command is executed with insufficient priveleges
    """
    def __init__(self, message=INSUFFICIENT_PRIVELEGES_MESSAGE):
        super().__init__(message)

class ImproperBufferSize(ValueError):
    """
    Raise an exception if the buffer size is not a root of 2
    """
    def __init__(self, message=BUFFER_EXCEPTION_MESSAGE):
        super().__init__(message)