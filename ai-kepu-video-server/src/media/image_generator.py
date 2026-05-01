"""
图片生成模块
基于豆包 seedream-4-0 API 生成 AI 图像
"""

import logging
import os
import time
import uuid
from pathlib import Path

import requests

from src.config import Config

logger = logging.getLogger(__name__)

# 风格预设（附加到 prompt 末尾）
STYLE_PRESETS = {
    "写实风格":   "photorealistic, cinematic lighting, 4k, high detail",
    "电影质感":   "cinematic lighting, film still, dramatic composition, high detail",
    "电影胶片":   "film grain, cinematic, anamorphic lens, vintage color grading, 35mm film",
    "吉卜力":     "soft pastel colors, warm sunlight, peaceful, dreamy, Studio Ghibli inspired",
    "治愈系":     "soft pastel colors, warm sunlight, peaceful, dreamy, Studio Ghibli inspired",
    "3D动画":     "3D animated film style, stylized characters, soft lighting, detailed environment",
    "赛博朋克":   "cyberpunk, neon lights, rainy night, futuristic city, blade runner aesthetic",
    "国风":       "Chinese ink painting, traditional brush strokes, misty mountains, elegant, minimalist",
    "水墨国风":   "Chinese ink painting, traditional brush strokes, misty mountains, elegant, minimalist",
    "油彩画":     "oil painting, visible brush strokes, rich colors, painterly texture, gallery quality",
    "毛毡风":     "felt craft art style, handmade felt texture, wool fabric, cute flat illustration, soft tactile surface, warm pastel tones, cozy miniature diorama look",
}


class ImageGenerator:
    """图片生成器 - 豆包 seedream-4-0"""

    def __init__(self, output_dir: str = "output/images"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.image_config = Config.image_config()
        self.api_url = self.image_config.get("api_url") or Config.SEEDREAM_API_URL
        self.api_key = self.image_config.get("api_key") or Config.SEEDREAM_API_KEY
        self.model = self.image_config.get("model") or Config.SEEDREAM_MODEL

    def generate(
        self,
        prompt: str,
        index: int = 0,
        width: int = 1920,
        height: int = 1080,
        style: str = "写实风格",
        style_suffix: str = None,
        filename: str = None,
    ) -> str:
        """
        生成 AI 图像，返回本地路径。

        Args:
            prompt: 英文图像描述
            index: 片段序号（用于文件命名）
            width: 图片宽度
            height: 图片高度
            style: 风格预设
            style_suffix: 自定义风格 prompt 后缀，优先级高于 style 预设
            filename: 自定义文件名（不含扩展名），如果为 None 则使用 segment_{index:03d}
        """
        if filename:
            output_path = self.output_dir / f"{filename}.jpg"
        else:
            output_path = self.output_dir / f"segment_{index:03d}.jpg"

        # 组合 prompt + 风格
        suffix = (style_suffix or "").strip() or STYLE_PRESETS.get(style, STYLE_PRESETS["写实风格"])
        full_prompt = f"{prompt}, {suffix}"

        # 尺寸映射（seedream 支持的规格）
        size = self._pick_size(width, height)

        logger.info(f"生成图像 [{index+1}]: {full_prompt[:60]}...")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        payload = {
            "model": self.model,
            "prompt": full_prompt,
            "size": size,
            "response_format": "url",
            "stream": False,
        }

        resp = None
        for attempt in range(3):
            try:
                resp = requests.post(self.api_url, headers=headers, json=payload, timeout=90)
                resp.raise_for_status()
                break
            except Exception as e:
                if attempt == 2:
                    raise
                logger.warning(f"图像生成失败（第{attempt+1}次），3秒后重试: {e}")
                time.sleep(3)
        data = resp.json()

        if not data.get("data"):
            raise RuntimeError(f"seedream 返回异常: {data}")

        img_url = data["data"][0]["url"]
        img_resp = requests.get(img_url, timeout=30)
        img_resp.raise_for_status()

        output_path.write_bytes(img_resp.content)
        logger.info(f"图像保存: {output_path} ({len(img_resp.content)} 字节)")
        return str(output_path)

    def _pick_size(self, width: int, height: int) -> str:
        """根据宽高比选择 seedream 支持的 size 参数"""
        ratio = width / height
        if ratio >= 1.6:
            return "1920x1080"  # 16:9 横版
        elif ratio <= 0.65:
            return "1080x1920"  # 9:16 竖版
        else:
            return "1k"         # 其他比例兜底


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    gen = ImageGenerator()
    path = gen.generate(
        prompt="A futuristic city with flying cars, golden hour, wide angle",
        index=0,
        style="电影胶片",
    )
    print(f"图片保存到: {path}")
