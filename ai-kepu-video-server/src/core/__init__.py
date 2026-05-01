"""
核心模块
包含项目管理和流水线编排
"""

from .project import VideoProject
from .pipeline import VideoEditorPipeline

__all__ = ['VideoProject', 'VideoEditorPipeline']
