"""
草稿构建模块
构建剪映草稿，添加特效、配音、字幕
"""

from .builder import DraftBuilder
from .voiceover import VoiceOverGenerator

try:
    from .template_engine import TemplateEngine
except ImportError:
    TemplateEngine = None

try:
    from .subtitle import SubtitleGenerator
except ImportError:
    SubtitleGenerator = None

__all__ = ['DraftBuilder', 'TemplateEngine', 'VoiceOverGenerator', 'SubtitleGenerator']
