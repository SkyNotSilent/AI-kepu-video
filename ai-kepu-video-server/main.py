"""
AI 自动剪辑工具 - 主入口
用法: python main.py [主题]
示例: python main.py 人工智能的未来
"""

import sys
import logging
import os

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)

from src.core.pipeline import VideoEditorPipeline


def main():
    if len(sys.argv) > 1:
        theme = " ".join(sys.argv[1:])
    else:
        theme = input("请输入视频主题: ").strip()
        if not theme:
            theme = "人工智能的未来"

    pipeline = VideoEditorPipeline(theme)
    draft_path = pipeline.run()
    print(f"\n[完成] 草稿已生成: {draft_path}")
    if pipeline.mp4_path:
        print(f"[完成] MP4 已导出: {pipeline.mp4_path}")
    print("请打开剪映，在草稿列表中找到该草稿，手动导出视频。")


if __name__ == "__main__":
    main()
