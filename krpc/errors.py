from enum import Enum
from typing import Any, Dict


class RpcErrorCode(Enum):
    PARSE_ERROR = (-32700, "Parse error")
    INVALID_REQUEST = (-32600, "Invalid Request")
    METHOD_NOT_FOUND = (-32601, "Method not found")
    INVALID_PARAMS = (-32602, "Invalid params")
    INTERNAL_ERROR = (-32603, "Internal error")
    UNSUPPORTED_CONTENT_TYPE = (-32700, "Unsupported Content-Type")


class RpcException(Exception):
    def __init__(self, code: int, message: str, data: Any = None):
        self.code = code
        self.message = message
        self.data = data
        super().__init__(self.message)

    @classmethod
    def parse(cls, error_code: RpcErrorCode | Enum, data: Any = None) -> Dict[str, Any]:
        return cls(code=error_code.value[0], message=error_code.value[1], data=data).to_dict

    @property
    def to_dict(self) -> Dict[str, Any]:
        return {
            'code': self.code,
            'message': self.message,
            'data': self.data
        }
