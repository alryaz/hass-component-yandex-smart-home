"""Errors for Yandex Smart Home."""
from typing import Optional
import inspect


class SmartHomeException(Exception):
    pass


class NotImplementedException(SmartHomeException):
    def __init__(self, cls):
        super(NotImplementedException, self).__init__(
            'Class %s does not implement %s'
            % (cls.__name__, inspect.stack()[1].function)
        )


class DefaultNotImplemented(NotImplementedException):
    pass


class OverrideNotImplemented(NotImplementedException):
    pass


class SmartHomeError(SmartHomeException):
    """Yandex Smart Home errors.

    https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/response-codes-docpage/
    """

    def __init__(self, code, msg):
        """Log error code."""
        super().__init__(msg)
        self.code = code
        self.message = msg
