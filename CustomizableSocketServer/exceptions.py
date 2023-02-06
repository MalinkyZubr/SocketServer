PASSWORD_LENGTH_EXCEPTION_MESSAGE = "Password length insufficient, 10 characters minimum"
AUTHENTICATION_FAILURE_EXCEPTION_MESSAGE = "Password authentication failure, incorrect password"
CONNECTION_NOT_FOUND_EXCEPTION_MESSAGE = "Connection wasnt found in the connections list"
INSUFFICIENT_PRIVELEGES_MESSAGE = "Not Authenticated: Need admin to execute this command"
BUFFER_EXCEPTION_MESSAGE = "The buffersize must be 2 raised to any power"


class PasswordLengthException(Exception):
    def __init__(self, message=PASSWORD_LENGTH_EXCEPTION_MESSAGE):
        super().__init__(message)


class AuthenticationFailure(Exception):
    def __init__(self, message=AUTHENTICATION_FAILURE_EXCEPTION_MESSAGE):
        super().__init__(message)


class ConnectionNotFoundError(Exception):
    def __init__(self, message=CONNECTION_NOT_FOUND_EXCEPTION_MESSAGE):
        super().__init__(message)


class InsufficientPriveleges(Exception):
    def __init__(self, message=INSUFFICIENT_PRIVELEGES_MESSAGE):
        super().__init__(message)

class ImproperBufferSize(ValueError):
    def __init__(self, message=BUFFER_EXCEPTION_MESSAGE):
        super().__init__(message)