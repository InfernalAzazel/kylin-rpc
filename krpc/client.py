import uuid
from typing import Any, Dict, Optional, Union, Awaitable
import httpx
from httpx import BaseTransport
from pydantic import BaseModel
from .message import Message, JsonMessage, message_management


class DictConfig(BaseModel):
    include: Optional[Union[set[int], set[str], dict[int, Any], dict[str, Any]]] = None
    exclude: Optional[Union[set[int], set[str], dict[int, Any], dict[str, Any]]] = None
    by_alias: bool = False
    exclude_unset: bool = True
    exclude_defaults: bool = False
    exclude_none: bool = False


class RpcClient:
    def __init__(
            self,
            url: str,
            rpc_media_type: str = 'json',
            cust_messages: Optional[Dict[str, Message]] = None,
            transport: BaseTransport | Any | None = None,
    ) -> None:
        """
        RPC客户端初始化。

        :param url: 所有请求URL。
        :param rpc_media_type: 消息编码类型，默认为 'json'。
        :param cust_messages: 自定义消息处理器字典。
        :param transport: （可选）用于通过网络发送请求的传输类。
        """
        self.url = url
        self.rpc_media_type = rpc_media_type
        self.messages = cust_messages or message_management
        self.client_sync = httpx.Client(transport=transport)
        self.client_async = httpx.AsyncClient(transport=transport)

    def close(self) -> None:
        """关闭同步和异步客户端的连接。"""
        self.client_sync.close()
        self.client_async.aclose()

    def _get_message(self) -> Message:
        """根据媒体类型获取消息编码器。"""
        return self.messages.get(self.rpc_media_type) or JsonMessage()

    def _prepare_request_data(
            self,
            method: str,
            params: Optional[Union[dict, BaseModel]] = None,
            dict_config: Optional[DictConfig] = None
    ) -> Dict[str, Any]:
        """准备请求的数据包，并处理 BaseModel 参数。"""
        if dict_config is None:
            dict_config = DictConfig()

        if isinstance(params, BaseModel):
            params = params.model_dump(
                include=dict_config.include,
                exclude=dict_config.exclude,
                by_alias=dict_config.by_alias,
                exclude_unset=dict_config.exclude_unset,
                exclude_defaults=dict_config.exclude_defaults,
                exclude_none=dict_config.exclude_none
            )

        request_data = {
            "method": method,
            "params": params or {},
            "id": str(uuid.uuid4())
        }
        message = self._get_message()
        return {
            'url': self.url,
            'content': message.encode(request_data),
            'headers': {'X-Krpc-Type': message.rpc_media_type}
        }

    def _send_request_base(
            self, client: Union[httpx.Client, httpx.AsyncClient],
            method: str,
            params: Optional[Union[dict, BaseModel]] = None,
            headers: Optional[Dict[str, str]] = None,
            dict_config: Optional[DictConfig] = None
    ) -> Union[httpx.Response, Awaitable[httpx.Response]]:
        """内部基础方法，根据客户端类型发送请求。"""
        request_kwargs = self._prepare_request_data(method, params, dict_config)
        if headers:
            request_kwargs['headers'].update(headers)
        if isinstance(client, httpx.Client):
            return client.post(**request_kwargs)
        else:
            async def send():
                async with client as client_async:
                    return await client_async.post(**request_kwargs)

            return send()

    def call(
            self,
            method: str,
            params: Optional[Union[dict, BaseModel]] = None,
            headers: Optional[dict[str, str]] = None,
            dict_config: Optional[DictConfig] = None
    ) -> Any:
        """
        同步调用RPC方法。
        """
        try:
            response = self._send_request_base(
                self.client_sync, method, params, headers, dict_config
            )
            message = self._get_message()
            data = message.decode(response.content)
        except Exception as e:
            data = {'error': str(e)}
        return data

    async def call_async(
            self,
            method: str,
            params: Optional[Union[dict, BaseModel]] = None,
            headers: Optional[Dict[str, str]] = None,
            dict_config: Optional[DictConfig] = None
    ) -> Any:
        """
        异步调用RPC方法。
        """
        try:
            response = await self._send_request_base(self.client_async, method, params, headers, dict_config)
            message = self._get_message()
            data = message.decode(response.content)
        except Exception as e:
            data = {'error': str(e)}
        return data

    def call_model(
            self,
            params: BaseModel,
            headers: dict[str, str] | None = None,
            dict_config: Optional[DictConfig] = None
    ) -> Any:
        """
        根据 `BaseModel` 子类实例中在 `Config` 类或 `model_config` 中声明的 `method_name`
        调用对应的RPC方法。

        Usage:

        1. 定义参数模型:
           首先，创建一个继承自 `BaseModel` 的类，并在其中定义所需的参数字段。
           同时，在该类的 `Config` 类或直接在 `model_config` 中设置 `method_name` 属性，
           指定要调用的RPC方法名。

           Example:

               >>> from pydantic import BaseModel, Field

               >>> class MyParams(BaseModel):

               >>>     my_param: str = Field(...)

               >>>     model_config = {"method_name": "my_rpc_method"}

        2. 调用 `call_mode`:
           使用上面定义的参数模型实例化对象，并将其传递给 `call_mode` 方法。
           客户端将根据模型中指定的 `method_name` 调用RPC服务。

           Example:

               >>> rpc_client = RpcClient(base_url="http://127.0.0.1:8000/api/v1/jsonrpc")
               >>> my_params = MyParams(my_param="Hello, RPC!")
               >>> response = rpc_client.call_model(my_params)

            Args:
                params (BaseModel): 包含方法调用所需参数和在模型配置中声明的 `method_name` 的 `BaseModel` 子类实例。
                headers (dict[str, str] | None):  请求头部
                dict_config (BaseModel): 用来过滤 BaseModel 模型字段 和 BaseModel.model_dump() 参数和效果都一致

            Returns:
                Any: RPC调用的结果。如果 `method_name` 未定义，则返回一个包含错误信息的字典。
            """

        method_name = params.model_config.get('method_name', '')
        if not method_name:
            data = {
                'error': 'The rpc client request parameter model has not yet set the '
                         'method_name method name under the Config class'
            }
            return data
        return self.call(str(method_name), params, headers, dict_config)

    async def call_model_async(
            self,
            params: BaseModel,
            headers: dict[str, str] | None = None,
            dict_config: Optional[DictConfig] = None
    ) -> Any:
        """
        根据 `BaseModel` 子类实例中在 `Config` 类或 `model_config` 中声明的 `method_name`
        异步调用对应的RPC方法。

        Usage:

        1. 定义参数模型:
           首先，创建一个继承自 `BaseModel` 的类，并在其中定义所需的参数字段。
           同时，在该类的 `Config` 类或直接在 `model_config` 中设置 `method_name` 属性，
           指定要调用的RPC方法名。

           - Example:

               >>> from pydantic import BaseModel, Field
               >>> import asyncio

               >>> class MyParams(BaseModel):

               >>>     my_param: str = Field(...)

               >>>     model_config = {"method_name": "my_rpc_method"}

        2. 调用 `call_model_async`:
           使用上面定义的参数模型实例化对象，并将其传递给 `call_model_async` 方法。
           客户端将根据模型中指定的 `method_name` 调用RPC服务。

           - Example:

               >>> async def main():
               >>>  rpc_client = RpcClient(base_url="http://127.0.0.1:8000/api/v1/jsonrpc")
               >>>  my_params = MyParams(my_param="Hello, RPC!")
               >>>  response = await rpc_client.call_model_async(my_params)
               >>> asyncio.run(main())

        Args:
            params (BaseModel): 包含方法调用所需参数和在模型配置中声明的 `method_name` 的 `BaseModel` 子类实例。
            headers (dict[str, str] | None):  请求头部
            dict_config (BaseModel): 用来过滤 BaseModel 模型字段 和 BaseModel.model_dump() 参数和效果都一致

        Returns:
            Any: RPC调用的结果。如果 `method_name` 未定义，则返回一个包含错误信息的字典。
        """
        method_name = params.model_config.get('method_name', '')
        if not method_name:
            return {
                'error': 'The rpc client request parameter model has not yet set the '
                         'method_name method name under the model_config class'
            }
        return await self.call_async(str(method_name), params, headers, dict_config)
