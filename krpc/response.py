from typing import Union, Any, Dict

from fastapi.encoders import jsonable_encoder

from .models import JsonRpcResponseModel


def JsonRPCResponse(
        response_id: Union[str, int, None] = None,
        result: Any = None,
        error: Union[Dict[str, Any], Any, None] = None,
):
    return jsonable_encoder(JsonRpcResponseModel(id=response_id, result=result, error=error))
