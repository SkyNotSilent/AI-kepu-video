"""
自动配音模块
基于豆包语音合成 API 生成中文语音
"""

import base64
import logging
import os
import time
import uuid
from pathlib import Path

import requests

from src.config import Config

logger = logging.getLogger(__name__)

DOUBAO_TTS_URL = "https://openspeech.bytedance.com/api/v1/tts"
DOUBAO_APPID   = Config.DOUBAO_TTS_APPID
DOUBAO_TOKEN   = Config.DOUBAO_TTS_TOKEN
DOUBAO_CLUSTER = "volcano_tts"
DOUBAO_VOICE   = "zh_male_jieshuoxiaoming_moon_bigtts"   # 默认音色


class VoiceOverGenerator:
    """配音生成器 - 豆包语音合成 TTS"""

    def __init__(self, output_dir: str = "output/voiceovers"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate(
        self,
        text: str,
        filename: str = None,
        voice_type: str = None,
        speed_ratio: float = 1.25,
        volume_ratio: float = 1.0,
    ) -> str:
        """
        生成配音，返回 wav 文件路径。

        Args:
            text: 文本内容
            filename: 输出文件名（不含扩展名）
            voice_type: 声音类型
            speed_ratio: 语速倍率，1.25 为默认（1.25倍速）
            volume_ratio: 音量倍率，1.0 为正常
        """
        if not filename:
            safe = "".join(c for c in text[:10] if c.isalnum() or c in "_ ")
            filename = safe.strip() or "voice"

        output_path = self.output_dir / f"{filename}.wav"
        logger.info(f"生成配音: {text[:30]}... -> {output_path}")
        logger.info(f"使用 TTS 配置 - APPID: {'已设置' if DOUBAO_APPID else '未设置'}, TOKEN: {'已设置' if DOUBAO_TOKEN else '未设置'}")

        voice = voice_type or DOUBAO_VOICE
        reqid = uuid.uuid4().hex

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer;{DOUBAO_TOKEN}",
        }
        payload = {
            "app": {"appid": DOUBAO_APPID, "token": DOUBAO_TOKEN, "cluster": DOUBAO_CLUSTER},
            "user": {"uid": "auto_video"},
            "audio": {
                "voice_type": voice,
                "encoding": "wav",
                "rate": 24000,
                "speed_ratio": speed_ratio,
                "volume_ratio": volume_ratio,
            },
            "request": {
                "reqid": reqid,
                "text": text,
                "operation": "query",
            },
        }

        for attempt in range(5):
            try:
                resp = requests.post(DOUBAO_TTS_URL, headers=headers, json=payload, timeout=30)
                if resp.status_code == 429:
                    wait = int(resp.headers.get("Retry-After", 30 * (attempt + 1)))
                    logger.warning(f"TTS 限流 429（第{attempt+1}次），等待 {wait}s 后重试")
                    time.sleep(wait)
                    continue
                resp.raise_for_status()
                break
            except requests.exceptions.HTTPError:
                raise
            except Exception as e:
                if attempt == 4:
                    raise
                wait = 10 * (attempt + 1)
                logger.warning(f"TTS 请求失败（第{attempt+1}次），{wait}s 后重试: {e}")
                time.sleep(wait)

        data = resp.json()
        if data.get("code") != 3000 or not data.get("data"):
            raise RuntimeError(f"豆包 TTS 失败: code={data.get('code')} msg={data.get('message')}")

        audio_bytes = base64.b64decode(data["data"])
        output_path.write_bytes(audio_bytes)

        logger.info(f"配音生成成功: {output_path} ({len(audio_bytes)} 字节)")
        return str(output_path)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    gen = VoiceOverGenerator()
    path = gen.generate("人工智能正在改变我们的世界，带来无限可能。", filename="test")
    print(f"音频保存到: {path}")
