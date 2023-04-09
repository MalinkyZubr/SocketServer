PASSWORD_LENGTH_EXCEPTION_MESSAGE = "Password length insufficient, 10 characters minimum"
AUTHENTICATION_FAILURE_EXCEPTION_MESSAGE = "Password authentication failure, incorrect password"
CONNECTION_NOT_FOUND_EXCEPTION_MESSAGE = "Connection wasnt found in the connections list"
INSUFFICIENT_PRIVELEGES_MESSAGE = "Not Authenticated: Need admin to execute this command"
BUFFER_EXCEPTION_MESSAGE = "The buffersize must be equal to 2 raised to any power"
FILE_NOT_ALLOWED_MESSAGE = "The file is not approved for download"
COMMAND_NOT_ALLOWED_MESSAGE = "Command execution is not permitted on this client"
AUTHENTICATION_PROCESS_NONEXISTANT_ERROR = "Authentication not required"
COMMAND_NOT_FOUND_MESSAGE = "Command not found"
COMMAND_ALREADY_EXISTS_MESSAGE = "Command already exists in the command list. Change its name"


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


class InsufficientPriveleges(AttributeError):
    """
    Raise an exception when a command is executed with insufficient priveleges
    """
    def __init__(self, message=INSUFFICIENT_PRIVELEGES_MESSAGE):
        super().__init__(message)

class ImproperBufferSize(BufferError):
    """
    Raise an exception if the buffer size is not a root of 2
    """
    def __init__(self, message=BUFFER_EXCEPTION_MESSAGE):
        super().__init__(message)


class FileNotApproved(FileNotFoundError):
    """
    Raise an exception if the received file is not approved for local download
    """
    def __init__(self, message=FILE_NOT_ALLOWED_MESSAGE):
        super().__init__(message)


class CommandExecutionNotAllowed(AttributeError):
    """
    Raise an exception when command execution is not allowed
    """
    def __init__(self, message=COMMAND_NOT_ALLOWED_MESSAGE):
        super().__init__(message)


class NoClientSideAuthentication(AttributeError):
    """
    Raise an exception when authentication process doesnt exist
    """
    def __init__(self, message=AUTHENTICATION_PROCESS_NONEXISTANT_ERROR):
        super().__init__(message)


class CommandNotFound(IndexError):
    """
    Raise an exception when requested command doesnt exist
    """
    def __init__(self, message=COMMAND_NOT_FOUND_MESSAGE):
        super().__init__(message)


class CommandAlreadyExists(AttributeError):
    """
    Raise an exception when requested command already exists
    """
    def __init__(self, message=COMMAND_ALREADY_EXISTS_MESSAGE):
        super().__init__(message)


class CommandExecutionError(Exception):
    """
    Raise an exception when command fails to execute
    """
    def __init__(self, help_menu):
        message = f"Command failed to execute due to incorrect parameters. If correct parameters were entered, please check function {help_menu}"
        super().__init__(message)