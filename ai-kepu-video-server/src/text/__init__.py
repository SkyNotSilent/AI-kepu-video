"""
文本处理模块
包含文章生成和文本分段功能
"""

from .generator import ArticleGenerator
from .segmenter import LongTextSegmenter, TextSegmenter
from .agents import ImagePromptAgent, ScriptRewriter

__all__ = ['ArticleGenerator', 'TextSegmenter', 'LongTextSegmenter', 'ScriptRewriter', 'ImagePromptAgent']
