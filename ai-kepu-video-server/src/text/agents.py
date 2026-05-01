"""
文本 Agent 模块
提供文案改写和逐段图片 prompt 生成能力。
"""

import json
import logging
import re
from typing import Optional

from .generator import ArticleGenerator

logger = logging.getLogger(__name__)


class ScriptRewriter:
    """文案改写 Agent - 将用户原文改写为旁白脚本，并生成总结"""

    def __init__(self, article_generator: Optional[ArticleGenerator] = None):
        self.article_generator = article_generator or ArticleGenerator()

    def rewrite(self, raw_text: str, style: str, target_length: int = None) -> dict:
        """
        输入用户原始文案，输出改写后的旁白脚本和 50-100 字内容总结。

        raw_text <= 200 字时视为主题，按主题生成脚本；raw_text > 200 字时
        视为用户剧本，尽量保持原意改写为适合配音的旁白。
        """
        raw_text = (raw_text or "").strip()
        if not raw_text:
            raise ValueError("文案不能为空")

        if len(raw_text) <= 200:
            prompt = self._theme_prompt(raw_text, style, target_length or 300)
        else:
            prompt = self._rewrite_prompt(raw_text, style)

        text = self.article_generator._call_api(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4096,
        )
        result = self._parse_json(text)
        script = (result.get("script") or "").strip()
        summary = (result.get("summary") or "").strip()

        if not script:
            raise RuntimeError(f"文案改写 Agent 返回缺少 script: {text[:200]}")
        if not summary:
            summary = self._fallback_summary(script)

        logger.info(f"文案改写完成: script={len(script)} 字, summary={len(summary)} 字")
        return {"script": script, "summary": summary}

    def _theme_prompt(self, theme: str, style: str, target_length: int) -> str:
        return f"""你是一位专业短视频旁白编剧。

请根据主题生成一篇适合配音朗读的中文短视频旁白脚本，并给出内容总结。

要求：
- 主题：{theme}
- 风格：{style}
- 目标长度：约 {target_length} 字
- 语言口语化，适合 TTS 配音
- 每个自然段 1-3 句话
- 不要标题、不要说明文字
- summary 为 50-100 字，概括全文核心内容

只输出 JSON，格式如下：
{{"script":"改写后的旁白脚本","summary":"50-100字内容总结"}}"""

    def _rewrite_prompt(self, raw_text: str, style: str) -> str:
        return f"""你是一位专业短视频旁白改写编剧。

请将用户提供的中文文案改写成适合视频解说和 TTS 配音的旁白脚本，并给出内容总结。

要求：
- 保持原文核心事实、观点和顺序，不要大幅改写含义
- 可以优化口语表达、节奏和衔接，让它更适合解说
- 风格：{style}
- 每个自然段 1-3 句话
- 不要标题、不要说明文字
- summary 为 50-100 字，概括全文核心内容

用户原文：
{raw_text}

只输出 JSON，格式如下：
{{"script":"改写后的旁白脚本","summary":"50-100字内容总结"}}"""

    def _parse_json(self, text: str) -> dict:
        text = (text or "").strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)
        if fenced:
            try:
                return json.loads(fenced.group(1))
            except json.JSONDecodeError:
                pass

        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            try:
                return json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                pass

        raise RuntimeError(f"无法解析 Agent JSON 输出: {text[:200]}")

    def _fallback_summary(self, script: str) -> str:
        compact = re.sub(r"\s+", "", script)
        return compact[:100]


class ImagePromptAgent:
    """图片 Prompt Agent - 逐段生成图片描述"""

    def __init__(self, article_generator: Optional[ArticleGenerator] = None):
        self.article_generator = article_generator or ArticleGenerator()

    def generate_prompt(self, segment_text: str, summary: str, style: str) -> str:
        """
        输入单段文案、全文总结和画面风格，输出不超过 30 个英文单词的图片 prompt。
        """
        user_prompt = f"""You are a professional AI image prompt writer.

Create one concise English image prompt for the current narration segment.

Full video summary:
{summary}

Current narration segment:
{segment_text}

Visual style constraint:
{style}

Requirements:
- English only
- 30 words or fewer
- Describe visible scene, subject, action, setting, mood, and composition
- No numbering, no explanation, no quotes
- Do not include text overlays or subtitles"""

        text = self.article_generator._call_api(
            messages=[{"role": "user", "content": user_prompt}],
            max_tokens=256,
        )
        prompt = self._clean_prompt(text)
        logger.info(f"图片 prompt 生成完成: {prompt}")
        return prompt

    def _clean_prompt(self, text: str) -> str:
        prompt = (text or "").strip()
        prompt = re.sub(r"^```(?:text)?\s*|\s*```$", "", prompt, flags=re.S).strip()
        prompt = prompt.splitlines()[0].strip() if "\n" in prompt else prompt
        prompt = re.sub(r"^\s*[-*\d.)]+\s*", "", prompt).strip()
        prompt = prompt.strip("\"'“”‘’")
        words = prompt.split()
        if len(words) > 30:
            prompt = " ".join(words[:30])
        if not prompt:
            prompt = "cinematic educational scene, clear subject, natural lighting, detailed composition"
        return prompt
