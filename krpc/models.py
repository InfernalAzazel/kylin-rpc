from typing import Any, Dict, Union, Optional

from pydantic import BaseModel, Field


class JsonRpcRequestModel(BaseModel):
    jsonrpc: str = "2.0"
    id: Union[str, int, None]
    method: str
    params: dict = Field(default_factory=dict)


class JsonRpcResponseModel(BaseModel):
    jsonrpc: str = "2.0"
    id: Union[str, int, None]
    result: Any = None
    error: Optional[Dict[str, Any]] = None


class JsonRpcErrorModel(BaseModel):
    code: int
    message: str
    data: Optional[Any] = None
