#!/usr/bin/env python3
"""
豆包TTS工具类 - 独立版本（无需额外依赖）
"""
import asyncio
import copy
import io
import json
import logging
import struct
import uuid
from dataclasses import dataclass
from enum import IntEnum
from typing import Optional, List

import websockets

logger = logging.getLogger(__name__)


# ==================== Protocol Definitions ====================

class MsgType(IntEnum):
    """消息类型"""
    Invalid = 0
    FullClientRequest = 0b1
    AudioOnlyClient = 0b10
    FullServerResponse = 0b1001
    AudioOnlyServer = 0b1011
    FrontEndResultServer = 0b1100
    Error = 0b1111

    def __str__(self) -> str:
        return self.name if self.name else f"MsgType({self.value})"


class MsgTypeFlagBits(IntEnum):
    """消息类型标志位"""
    NoSeq = 0
    PositiveSeq = 0b1
    LastNoSeq = 0b10
    NegativeSeq = 0b11
    WithEvent = 0b100


class VersionBits(IntEnum):
    """版本位"""
    Version1 = 1


class HeaderSizeBits(IntEnum):
    """头部大小位"""
    HeaderSize4 = 1


class SerializationBits(IntEnum):
    """序列化方法位"""
    Raw = 0
    JSON = 0b1
    Thrift = 0b11
    Custom = 0b1111


class CompressionBits(IntEnum):
    """压缩方法位"""
    None_ = 0


class EventType(IntEnum):
    """事件类型"""
    None_ = 0
    StartConnection = 1
    FinishConnection = 2
    ConnectionStarted = 50
    ConnectionFailed = 51
    ConnectionFinished = 52
    StartSession = 100
    FinishSession = 102
    SessionStarted = 150
    SessionFinished = 152
    TaskRequest = 200

    # TTS events
    TTSSentenceStart = 350
    TTSSentenceEnd = 351
    TTSResponse = 352
    TTSEnded = 359

    def __str__(self) -> str:
        return self.name if self.name else f"EventType({self.value})"


@dataclass
class Message:
    """消息对象"""
    version: VersionBits = VersionBits.Version1
    header_size: HeaderSizeBits = HeaderSizeBits.HeaderSize4
    type: MsgType = MsgType.Invalid
    flag: MsgTypeFlagBits = MsgTypeFlagBits.NoSeq
    serialization: SerializationBits = SerializationBits.JSON
    compression: CompressionBits = CompressionBits.None_
    sequence: int = 0
    event: EventType = EventType.None_
    session_id: str = ""
    payload: bytes = b""

    def marshal(self) -> bytes:
        """序列化消息"""
        buf = io.BytesIO()

        # 写入基础头部
        header = [
            (self.version << 4) | self.header_size,
            (self.type << 4) | self.flag,
            (self.serialization << 4) | self.compression,
        ]

        # 填充到header_size指定的大小
        header_size = 4 * self.header_size
        if padding := header_size - len(header):
            header.extend([0] * padding)

        buf.write(bytes(header))

        # 写入event和session_id (如果有WithEvent标志)
        if self.flag == MsgTypeFlagBits.WithEvent:
            buf.write(struct.pack(">i", self.event))

            # 只有非连接事件才写入session_id
            if self.event not in [
                EventType.StartConnection,
                EventType.FinishConnection,
                EventType.ConnectionStarted,
                EventType.ConnectionFailed,
            ]:
                session_id_bytes = self.session_id.encode("utf-8")
                buf.write(struct.pack(">I", len(session_id_bytes)))
                if session_id_bytes:
                    buf.write(session_id_bytes)

        # 写入sequence (如果需要)
        if self.type in [
            MsgType.FullClientRequest,
            MsgType.FullServerResponse,
            MsgType.FrontEndResultServer,
            MsgType.AudioOnlyClient,
            MsgType.AudioOnlyServer,
        ]:
            if self.flag in [MsgTypeFlagBits.PositiveSeq, MsgTypeFlagBits.NegativeSeq]:
                buf.write(struct.pack(">i", self.sequence))

        # 写入payload (带长度前缀)
        payload_size = len(self.payload)
        buf.write(struct.pack(">I", payload_size))
        buf.write(self.payload)

        return buf.getvalue()

    @staticmethod
    def unmarshal(data: bytes) -> "Message":
        """反序列化消息"""
        if len(data) < 3:
            raise ValueError("Invalid message: too short")

        buf = io.BytesIO(data)

        # 读取基础头部
        version_and_header_size = buf.read(1)[0]
        msg = Message()
        msg.version = VersionBits(version_and_header_size >> 4)
        msg.header_size = HeaderSizeBits(version_and_header_size & 0x0F)

        type_and_flag = buf.read(1)[0]
        msg.type = MsgType(type_and_flag >> 4)
        msg.flag = MsgTypeFlagBits(type_and_flag & 0x0F)

        serialization_compression = buf.read(1)[0]
        msg.serialization = SerializationBits(serialization_compression >> 4)
        msg.compression = CompressionBits(serialization_compression & 0x0F)

        # 跳过header padding
        header_size = 4 * msg.header_size
        read_size = 3
        if padding_size := header_size - read_size:
            buf.read(padding_size)

        # 读取sequence (如果需要)
        if msg.type in [
            MsgType.FullClientRequest,
            MsgType.FullServerResponse,
            MsgType.FrontEndResultServer,
            MsgType.AudioOnlyClient,
            MsgType.AudioOnlyServer,
        ]:
            if msg.flag in [MsgTypeFlagBits.PositiveSeq, MsgTypeFlagBits.NegativeSeq]:
                seq_bytes = buf.read(4)
                if len(seq_bytes) == 4:
                    msg.sequence = struct.unpack(">i", seq_bytes)[0]

        # 读取event和session_id (如果有WithEvent标志)
        if msg.flag == MsgTypeFlagBits.WithEvent:
            event_bytes = buf.read(4)
            if len(event_bytes) == 4:
                msg.event = EventType(struct.unpack(">i", event_bytes)[0])

            # 只有非连接事件才读取session_id
            if msg.event not in [
                EventType.StartConnection,
                EventType.FinishConnection,
                EventType.ConnectionStarted,
                EventType.ConnectionFailed,
                EventType.ConnectionFinished,
            ]:
                size_bytes = buf.read(4)
                if len(size_bytes) == 4:
                    session_id_len = struct.unpack(">I", size_bytes)[0]
                    if session_id_len > 0:
                        session_id_bytes = buf.read(session_id_len)
                        msg.session_id = session_id_bytes.decode("utf-8")

            # 读取connect_id (只在特定连接事件中)
            if msg.event in [
                EventType.ConnectionStarted,
                EventType.ConnectionFailed,
                EventType.ConnectionFinished,
            ]:
                connect_id_size_bytes = buf.read(4)
                if len(connect_id_size_bytes) == 4:
                    connect_id_len = struct.unpack(">I", connect_id_size_bytes)[0]
                    if connect_id_len > 0:
                        buf.read(connect_id_len)  # 跳过connect_id

        # 读取payload (带长度前缀)
        payload_size_bytes = buf.read(4)
        if len(payload_size_bytes) == 4:
            payload_size = struct.unpack(">I", payload_size_bytes)[0]
            if payload_size > 0:
                msg.payload = buf.read(payload_size)

        return msg

    def __str__(self) -> str:
        parts = [f"type={self.type}"]
        if self.flag & MsgTypeFlagBits.WithEvent:
            parts.append(f"event={self.event}")
        if self.session_id:
            parts.append(f"session_id={self.session_id[:8]}...")
        if self.payload and self.type != MsgType.AudioOnlyServer:
            try:
                payload_str = self.payload.decode("utf-8")
                if len(payload_str) > 100:
                    payload_str = payload_str[:100] + "..."
                parts.append(f"payload={payload_str}")
            except:
                parts.append(f"payload=<{len(self.payload)} bytes>")
        elif self.payload:
            parts.append(f"audio=<{len(self.payload)} bytes>")

        return f"Message({', '.join(parts)})"


# ==================== Protocol Functions ====================

async def receive_message(websocket) -> Message:
    """接收消息"""
    data = await websocket.recv()
    msg = Message.unmarshal(data)
    logger.debug(f"Received: {msg}")
    return msg


async def wait_for_event(websocket, msg_type: MsgType, event: EventType) -> Message:
    """等待特定事件"""
    while True:
        msg = await receive_message(websocket)
        if msg.type == msg_type and msg.event == event:
            return msg
        if msg.type == MsgType.Error:
            try:
                error_info = msg.payload.decode("utf-8") if msg.payload else "Unknown error"
            except UnicodeDecodeError:
                error_info = f"Binary error data: {msg.payload.hex()}"
            raise RuntimeError(f"Server error: {error_info}")


async def start_connection(websocket) -> None:
    """开始连接"""
    msg = Message(type=MsgType.FullClientRequest, flag=MsgTypeFlagBits.WithEvent)
    msg.event = EventType.StartConnection
    msg.payload = b"{}"
    logger.info(f"Sending: {msg}")
    await websocket.send(msg.marshal())


async def finish_connection(websocket) -> None:
    """结束连接"""
    msg = Message(type=MsgType.FullClientRequest, flag=MsgTypeFlagBits.WithEvent)
    msg.event = EventType.FinishConnection
    msg.payload = b"{}"
    logger.info(f"Sending: {msg}")
    await websocket.send(msg.marshal())


async def start_session(websocket, payload: bytes, session_id: str) -> None:
    """开始会话"""
    msg = Message(type=MsgType.FullClientRequest, flag=MsgTypeFlagBits.WithEvent)
    msg.event = EventType.StartSession
    msg.session_id = session_id
    msg.payload = payload
    logger.info(f"Sending: {msg}")
    await websocket.send(msg.marshal())


async def finish_session(websocket, session_id: str) -> None:
    """结束会话"""
    msg = Message(type=MsgType.FullClientRequest, flag=MsgTypeFlagBits.WithEvent)
    msg.event = EventType.FinishSession
    msg.session_id = session_id
    msg.payload = b"{}"
    logger.info(f"Sending: {msg}")
    await websocket.send(msg.marshal())


async def task_request(websocket, payload: bytes, session_id: str) -> None:
    """发送任务请求"""
    msg = Message(type=MsgType.FullClientRequest, flag=MsgTypeFlagBits.WithEvent)
    msg.event = EventType.TaskRequest
    msg.session_id = session_id
    msg.payload = payload
    logger.debug(f"Sending: {msg}")
    await websocket.send(msg.marshal())


# ==================== TTS Client ====================

class VolcengineTTS:
    """豆包TTS客户端"""

    DEFAULT_ENDPOINT = "wss://openspeech.bytedance.com/api/v3/tts/bidirection"

    def __init__(
        self,
        appid: str,
        access_token: str,
        resource_id: Optional[str] = None,
        endpoint: Optional[str] = None,
    ):
        """
        初始化TTS客户端

        Args:
            appid: APP ID
            access_token: Access Token
            resource_id: Resource ID (可选，会根据voice_type自动推断)
            endpoint: WebSocket端点URL (可选)
        """
        self.appid = appid
        self.access_token = access_token
        self.resource_id = resource_id
        self.endpoint = endpoint or self.DEFAULT_ENDPOINT
        self.websocket = None

    @staticmethod
    def get_resource_id(voice_type: str) -> str:
        """根据音色类型获取Resource ID"""
        if voice_type.startswith("S_"):
            return "volc.megatts.default"
        return "volc.service_type.10029"

    async def connect(self, voice_type: str) -> None:
        """建立WebSocket连接"""
        headers = {
            "X-Api-App-Key": self.appid,
            "X-Api-Access-Key": self.access_token,
            "X-Api-Resource-Id": (
                self.resource_id if self.resource_id else self.get_resource_id(voice_type)
            ),
            "X-Api-Connect-Id": str(uuid.uuid4()),
        }

        logger.info(f"Connecting to {self.endpoint}")
        self.websocket = await websockets.connect(
            self.endpoint, additional_headers=headers, max_size=10 * 1024 * 1024
        )
        logger.info(
            f"Connected, Logid: {self.websocket.response.headers.get('x-tt-logid', 'N/A')}"
        )

        await start_connection(self.websocket)

        # 等待连接确认，如果失败会抛出异常
        try:
            await wait_for_event(
                self.websocket, MsgType.FullServerResponse, EventType.ConnectionStarted
            )
            logger.info("Connection established successfully")
        except Exception as e:
            await self.websocket.close()
            raise RuntimeError(f"Failed to establish connection. Please check your appid, access_token, and voice_type. Error: {e}")

    async def close(self) -> None:
        """关闭连接"""
        if self.websocket:
            try:
                await finish_connection(self.websocket)
                await wait_for_event(
                    self.websocket, MsgType.FullServerResponse, EventType.ConnectionFinished
                )
            except Exception as e:
                logger.warning(f"Error during connection close: {e}")
            finally:
                try:
                    await self.websocket.close()
                except:
                    pass
                logger.info("Connection closed")

    async def synthesize(
        self,
        text: str,
        voice_type: str,
        encoding: str = "mp3",
        sample_rate: int = 24000,
        char_delay: float = 0.005,
        disable_markdown_filter: bool = False,
    ) -> bytes:
        """
        合成单个文本片段

        Args:
            text: 要合成的文本
            voice_type: 音色类型
            encoding: 音频编码格式 (mp3/wav/pcm等)
            sample_rate: 采样率
            char_delay: 字符间延迟(秒)
            disable_markdown_filter: 是否禁用markdown过滤

        Returns:
            音频数据(bytes)
        """
        base_request = {
            "user": {"uid": str(uuid.uuid4())},
            "namespace": "BidirectionalTTS",
            "req_params": {
                "speaker": voice_type,
                "audio_params": {
                    "format": encoding,
                    "sample_rate": sample_rate,
                    "enable_timestamp": True,
                },
                "additions": json.dumps({
                    "disable_markdown_filter": disable_markdown_filter,
                }),
            },
        }

        # 开始会话
        start_session_request = copy.deepcopy(base_request)
        start_session_request["event"] = EventType.StartSession
        session_id = str(uuid.uuid4())

        await start_session(
            self.websocket, json.dumps(start_session_request).encode(), session_id
        )
        await wait_for_event(
            self.websocket, MsgType.FullServerResponse, EventType.SessionStarted
        )

        # 逐字符发送
        async def send_chars():
            for char in text:
                synthesis_request = copy.deepcopy(base_request)
                synthesis_request["event"] = EventType.TaskRequest
                synthesis_request["req_params"]["text"] = char
                await task_request(
                    self.websocket, json.dumps(synthesis_request).encode(), session_id
                )
                await asyncio.sleep(char_delay)

            await finish_session(self.websocket, session_id)

        # 后台发送任务
        send_task = asyncio.create_task(send_chars())

        # 接收音频数据
        audio_data = bytearray()
        while True:
            msg = await receive_message(self.websocket)

            if msg.type == MsgType.FullServerResponse:
                if msg.event == EventType.SessionFinished:
                    break
            elif msg.type == MsgType.AudioOnlyServer:
                audio_data.extend(msg.payload)
            else:
                raise RuntimeError(f"TTS conversion failed: {msg}")

        await send_task

        logger.info(f"Audio received: {len(audio_data)} bytes")
        return bytes(audio_data)

    async def synthesize_text(
        self,
        text: str,
        voice_type: str,
        encoding: str = "mp3",
        sample_rate: int = 24000,
        split_by: str = "。",
    ) -> List[bytes]:
        """
        合成完整文本(自动按句子分割)

        Args:
            text: 要合成的完整文本
            voice_type: 音色类型
            encoding: 音频编码格式
            sample_rate: 采样率
            split_by: 分句符号

        Returns:
            音频数据列表
        """
        sentences = [s for s in text.split(split_by) if s.strip()]
        audio_list = []

        for sentence in sentences:
            audio_data = await self.synthesize(
                sentence, voice_type, encoding, sample_rate
            )
            if audio_data:
                audio_list.append(audio_data)

        return audio_list


async def text_to_speech(
    text: str,
    appid: str,
    access_token: str,
    voice_type: str,
    output_file: Optional[str] = None,
    encoding: str = "mp3",
    resource_id: Optional[str] = None,
) -> bytes:
    """
    便捷函数：文本转语音

    Args:
        text: 要合成的文本
        appid: APP ID
        access_token: Access Token
        voice_type: 音色类型
        output_file: 输出文件路径(可选)
        encoding: 音频编码格式
        resource_id: Resource ID(可选)

    Returns:
        音频数据
    """
    tts = VolcengineTTS(appid, access_token, resource_id)

    try:
        await tts.connect(voice_type)
        audio_list = await tts.synthesize_text(text, voice_type, encoding)

        # 合并所有音频
        audio_data = b"".join(audio_list)

        # 保存文件
        if output_file:
            with open(output_file, "wb") as f:
                f.write(audio_data)
            logger.info(f"Audio saved to {output_file}")

        return audio_data

    finally:
        await tts.close()


# ==================== 使用示例 ====================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # 示例1: 使用便捷函数 - 请根据你的控制台配置修改参数
    async def example1():
        """
        使用说明：
        1. 登录豆包TTS控制台: https://console.volcengine.com/speech/service
        2. 查看你的应用详情，获取：
           - appid (应用ID)
           - access_token (访问令牌)
           - 可用的音色列表和对应的resource_id
        3. 修改下面的参数后运行
        """

        # TODO: 请根据你的控制台配置修改这些参数
        audio = await text_to_speech(
            text="你好，这是一个测试。",
            appid="",  # 你的APP ID
            access_token="",  # 你的Access Token
            voice_type="zh_male_jieshuoxiaoming_uranus_bigtts",  # 从控制台获取可用的音色
            resource_id="seed-tts-2.0",  # 从控制台获取对应的resource_id
            output_file="22.mp3",
        )
        print(f"SUCCESS: Generated {len(audio)} bytes")
        print(f"Audio saved to output.mp3")

    # 示例2: 使用类接口
    async def example2():
        # 请替换成你的真实凭证
        tts = VolcengineTTS(
            appid="",
            access_token="",
        )

        try:
            await tts.connect("zh_female_qingxin")

            # 合成单个句子
            audio = await tts.synthesize(
                "这是第一句话",
                voice_type="zh_female_qingxin",
            )

            # 合成完整文本
            audio_list = await tts.synthesize_text(
                "第一句。第二句。第三句。",
                voice_type="zh_female_qingxin",
            )

        finally:
            await tts.close()

    # 运行示例
    asyncio.run(example1())
