class PasswordLengthException(Exception):
    def __init__(self, message=None):
        if not message:
            message = "Password length insufficient, 10 characters minimum"
        super().__init__(message)


class AuthenticationFailure(Exception):
    def __init__(self, message=None):
        if not message:
            message = "Password authentication failure, incorrect password"
        super().__init__(message)


class ConnectionNotFoundError(Exception):
    def __init__(self, message=None):
        if not message:
            message = "Connection wasnt found in the connections list"
        super().__init__(message)


class InsufficientPriveleges(Exception):
    def __init__(self, message=None):
        if not message:
            message = "Not Authenticated: Need admin to execute this command"
        super().__init__(message)

class ImproperBufferSize(ValueError):
    def __init__(self, message=None):
        if not message:
            message = "The buffersize must be 2 raised to any power"
        super().__init__(message)