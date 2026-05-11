"""
文章生成模块
基于 LLM API 生成高质量视频脚本
"""

import json
import logging
from pathlib import Path

import requests

from src.config import Config

logger = logging.getLogger(__name__)


class ArticleGenerator:
    """文章生成器 - 基于 LLM API"""

    def __init__(self, config_path: str = "config/prompts/article_generation.json"):
        self.config_path = Path(config_path)
        self.prompt_config = self._load_config()
        self.llm_config = Config.llm_config()
        self.protocol = (self.llm_config.get("protocol") or "anthropic").lower()
        self.api_key = self.llm_config.get("api_key") or ""
        self.model = self.llm_config.get("model") or Config.LLM_MODEL or Config.ANTHROPIC_MODEL
        self.api_url = self._build_api_url(
            self.llm_config.get("base_url") or Config.LLM_BASE_URL or Config.ANTHROPIC_BASE_URL
        )

        if not self.api_key:
            raise ValueError("LLM API Key 未配置")

        self.headers = self._build_headers()

    def _load_config(self) -> dict:
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {
                "system": "你是一位专业的短视频脚本作家，擅长创作引人入胜、情感丰富的内容。",
                "user": "请为主题「{theme}」写一篇约{length}字的短视频旁白脚本。风格：{style}。要求：每个自然段只有1-2句话，语言口语化，适合配音朗读。直接输出脚本正文，不要标题和说明。",
            }

    def _build_api_url(self, base_url: str) -> str:
        base = (base_url or "").rstrip("/")
        if self.protocol == "openai":
            if base.endswith("/chat/completions"):
                return base
            if base.endswith("/v1"):
                return f"{base}/chat/completions"
            return f"{base}/v1/chat/completions"

        if base.endswith("/messages"):
            return base
        if base.endswith("/v1"):
            return f"{base}/messages"
        return f"{base}/v1/messages"

    def _build_headers(self) -> dict:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        if self.protocol != "openai":
            headers["x-api-key"] = self.api_key
            headers["anthropic-version"] = "2023-06-01"
        return headers

    def _call_api(self, messages: list, max_tokens: int = 2048) -> str:
        import time
        if self.protocol == "openai":
            payload = {
                "model": self.model,
                "messages": messages,
                "max_tokens": max_tokens,
            }
        else:
            payload = {
                "model": self.model,
                "max_tokens": max_tokens,
                "messages": messages,
            }

        # 重试机制：最多尝试 3 次
        for attempt in range(3):
            try:
                resp = requests.post(self.api_url, headers=self.headers, json=payload, timeout=120)
                resp.raise_for_status()
                data = resp.json()
                return self._extract_text(data)
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                if attempt == 2:  # 最后一次尝试失败
                    logger.error(f"API 调用失败，已重试 3 次: {e}")
                    raise
                wait_time = (attempt + 1) * 5  # 5秒、10秒
                logger.warning(f"API 调用失败（第 {attempt + 1} 次），{wait_time} 秒后重试: {e}")
                time.sleep(wait_time)
            except requests.exceptions.HTTPError as e:
                # HTTP 错误不重试（如 401、403、429 等）
                logger.error(f"API HTTP 错误: {e}")
                raise

    def _extract_text(self, data: dict) -> str:
        """兼容 Anthropic Messages 与 OpenAI Chat Completions 的常见返回格式。"""
        if self.protocol == "openai":
            choice = (data.get("choices") or [{}])[0]
            message = choice.get("message") or {}
            content = message.get("content")
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                parts = []
                for item in content:
                    if isinstance(item, dict):
                        parts.append(item.get("text") or item.get("content") or "")
                    elif isinstance(item, str):
                        parts.append(item)
                text = "".join(parts).strip()
                if text:
                    return text
            if choice.get("text"):
                return choice["text"]
            raise RuntimeError(f"OpenAI 兼容接口返回缺少文本内容: {data}")

        content = data.get("content")
        if isinstance(content, list):
            text = "".join(
                item.get("text", "") if isinstance(item, dict) else str(item)
                for item in content
            ).strip()
            if text:
                return text
        if isinstance(content, str):
            return content
        raise RuntimeError(f"Anthropic 兼容接口返回缺少文本内容: {data}")

    def generate(
        self,
        theme: str,
        length: int = 300,
        style: str = "温暖感人",
        platform: str = "短视频平台",
    ) -> str:
        logger.info(f"生成文章: 主题={theme}, 长度={length}")

        system_prompt = self.prompt_config.get("system", "")
        user_prompt = self.prompt_config.get("user", "").format(
            theme=theme, length=length, style=style, platform=platform
        )

        combined_prompt = f"{system_prompt}\n\n{user_prompt}" if system_prompt else user_prompt

        article = self._call_api(
            messages=[{"role": "user", "content": combined_prompt}],
            max_tokens=2048,
        )
        logger.info(f"文章生成成功，长度: {len(article)} 字")
        return article

    def generate_image_prompts(self, segments: list, style: str = "写实风格") -> list:
        """为每个文本段落生成对应的英文图像 prompt"""
        logger.info(f"生成图像 prompts，共 {len(segments)} 段")

        segments_text = "\n".join(f"{i+1}. {s}" for i, s in enumerate(segments))
        user_prompt = f"""以下是一个短视频的分段旁白文本，请为每段生成一个简洁的英文图像描述（image prompt），用于 AI 图像生成。

要求：
- 每段对应一个 prompt，直接描述画面内容
- 英文输出，不超过 20 个单词
- 风格参考：{style}
- 只输出 prompt 列表，每行一个，不要序号和解释

旁白分段：
{segments_text}"""

        text = self._call_api(
            messages=[{"role": "user", "content": user_prompt}],
            max_tokens=1024,
        )

        lines = [l.strip() for l in text.strip().splitlines() if l.strip()]
        while len(lines) < len(segments):
            lines.append(f"cinematic scene related to: {segments[len(lines)][:30]}")
        return lines[:len(segments)]


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    gen = ArticleGenerator()
    print(gen.generate("人工智能的未来"))
