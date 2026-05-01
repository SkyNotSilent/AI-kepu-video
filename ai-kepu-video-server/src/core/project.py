"""
项目管理模块
管理视频项目
"""

import json
import logging
from typing import Dict, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class VideoProject:
    """视频项目管理器"""
    
    def __init__(self, theme: str, config_path: str = "config/settings.json"):
        """
        初始化视频项目
        
        Args:
            theme: 主题
            config_path: 配置文件路径
        """
        self.theme = theme
        self.config_path = Path(config_path)
        self.config = self._load_config()
        
        # 项目状态
        self.article = None
        self.segments = []
        self.media_paths = []
        self.voiceover_files = []
        self.subtitle_files = []
        self.draft_path = None
        
    def _load_config(self) -> dict:
        """加载配置"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载配置失败: {e}")
            return {}
    
    def set_article(self, article: str):
        """设置文章"""
        self.article = article
        logger.info("文章已设置")
    
    def add_segment(self, text: str):
        """添加段落"""
        self.segments.append(text)
        logger.info(f"添加段落: {text[:50]}...")
    
    def add_media(self, path: str):
        """添加媒体文件"""
        self.media_paths.append(path)
        logger.info(f"添加媒体: {path}")
    
    def add_voiceover(self, path: str):
        """添加配音文件"""
        self.voiceover_files.append(path)
        logger.info(f"添加配音: {path}")
    
    def add_subtitle(self, path: str):
        """添加字幕文件"""
        self.subtitle_files.append(path)
        logger.info(f"添加字幕: {path}")
    
    def set_draft_path(self, path: str):
        """设置草稿路径"""
        self.draft_path = path
        logger.info(f"草稿路径已设置: {path}")
    
    def get_status(self) -> dict:
        """获取项目状态"""
        return {
            "theme": self.theme,
            "article": self.article is not None,
            "segments_count": len(self.segments),
            "media_count": len(self.media_paths),
            "voiceover_count": len(self.voiceover_files),
            "subtitle_count": len(self.subtitle_files),
            "draft_path": self.draft_path
        }
    
    def save_project(self, output_path: str):
        """保存项目"""
        project_data = {
            "theme": self.theme,
            "article": self.article,
            "segments": self.segments,
            "media_paths": self.media_paths,
            "voiceover_files": self.voiceover_files,
            "subtitle_files": self.subtitle_files,
            "draft_path": self.draft_path
        }
        
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(project_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"项目已保存: {output_path}")


if __name__ == "__main__":
    # 测试代码
    project = VideoProject("人工智能的未来")
    
    # 设置文章
    project.set_article("这是文章内容...")
    
    # 添加段落
    project.add_segment("第一段文字")
    project.add_segment("第二段文字")
    
    # 添加媒体
    project.add_media("image1.jpg")
    
    # 获取状态
    status = project.get_status()
    print("项目状态:", status)
