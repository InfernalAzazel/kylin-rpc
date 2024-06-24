from typing import Any, Dict, Union, Optional
from pydantic import BaseModel, Field


class RpcRequestModel(BaseModel):
    id: Union[str, int, None]
    method: str
    params: Dict = Field(default_factory=Dict)


class RpcResponseModel(BaseModel):
    id: Union[str, int, None]
    result: Any = None
    error: Optional[Dict[str, Any]] = None
