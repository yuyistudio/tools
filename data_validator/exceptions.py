# coding: utf8


class BaseException(Exception):
    pass


class ValidationException(BaseException):
    pass


# contains the message for end-users.
class MessageException(BaseException):
    pass


# raise the Exception to stop validation of the current executing schema.
class IgnoredSchemaException(BaseException):
    pass


class ConfigException(BaseException):
    pass


class FieldTypeException(BaseException):
    pass


class KeyNotFoundException(BaseException):
    pass


class OneOfKeyFoundException(BaseException):
    pass


# stop following validations, and mark validation success.
class StopValidation(BaseException):
    pass
