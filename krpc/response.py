from typing import Union, Any, Dict

from fastapi.encoders import jsonable_encoder

from .models import RpcResponseModel


def EncoderModelResponse(
        response_id: Union[str, int, None] = None,
        result: Any = None,
        error: Union[Dict[str, Any], Any, None] = None,
):
    return jsonable_encoder(RpcResponseModel(id=response_id, result=result, error=error))
