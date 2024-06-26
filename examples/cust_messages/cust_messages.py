import io
import json
from typing import Any, Dict
from krpc import Message, message_management
import gzip


# 自定义加解码器
class GzipJsonMessage(Message):
    rpc_media_type = "gzip-json"

    def decode(self, data: bytes) -> Dict[str, Any] | None:
        """
        使用gzip解压缩数据，并尝试将其反序列化为字典
        :param data: 压缩的字节数据
        :return: 反序列化后的字典
        """
        # 使用gzip解压缩
        buffer = io.BytesIO(data)
        with gzip.GzipFile(fileobj=buffer, mode='rb') as un_gzipped_data:
            data_json_bytes = un_gzipped_data.read()

        # 将解压缩后的字节串反序列化为字典
        data_dict = json.loads(data_json_bytes.decode('utf-8'))
        return data_dict

    def encode(self, data: Dict[str, Any]) -> bytes | None:
        # 将字典转换为JSON格式的字节串
        data_json_bytes = json.dumps(data).encode('utf-8')
        buffer = io.BytesIO()
        with gzip.GzipFile(fileobj=buffer, mode='w') as gzipped_data:
            gzipped_data.write(data_json_bytes)
        return buffer.getvalue()


# 添加 GzipJsonMessage 实例到 message_management 字典中
message_management['gzip-json'] = GzipJsonMessage()
