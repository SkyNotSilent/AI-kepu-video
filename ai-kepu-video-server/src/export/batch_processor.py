"""
批量处理器
批量处理多个主题
"""

import logging
from typing import List
from pathlib import Path

logger = logging.getLogger(__name__)


class BatchProcessor:
    """批量处理器 - 批量处理多个主题"""
    
    def __init__(self, themes: List[str], output_dir: str = "output"):
        """
        初始化批量处理器
        
        Args:
            themes: 主题列表
            output_dir: 输出目录
        """
        self.themes = themes
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def run(self):
        """运行批量处理"""
        logger.info(f"开始批量处理: {len(self.themes)} 个主题")
        
        for i, theme in enumerate(self.themes, 1):
            logger.info(f"处理第 {i}/{len(self.themes)} 个主题: {theme}")
            
            try:
                # TODO: 调用主流程
                # from src.core.pipeline import VideoEditorPipeline
                # editor = VideoEditorPipeline(theme)
                # editor.run()
                
                logger.info(f"主题 {theme} 处理完成")
                
            except Exception as e:
                logger.error(f"主题 {theme} 处理失败: {e}")
                continue
        
        logger.info("批量处理完成")


if __name__ == "__main__":
    # 测试代码
    themes = ["人工智能", "机器学习", "深度学习"]
    processor = BatchProcessor(themes)
    
    # processor.run()
