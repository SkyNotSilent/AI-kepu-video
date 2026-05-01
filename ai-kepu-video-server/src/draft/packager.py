"""
草稿打包器
将剪映草稿及其素材打包成可移植的压缩包
"""

import json
import logging
import shutil
import zipfile
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)


class DraftPackager:
    """草稿打包器 - 将草稿和素材打包成可移植的压缩包"""

    def __init__(self):
        pass

    def package(
        self,
        draft_path: str,
        output_zip: str = None,
        cleanup_original: bool = False,
        copy_materials: bool = True,
    ) -> str:
        """
        打包草稿及其素材

        Args:
            draft_path: 草稿目录路径
            output_zip: 输出压缩包路径（默认为 draft_path.zip）
            cleanup_original: 是否删除原始草稿目录
            copy_materials: 是否复制素材到草稿目录（如果素材已在草稿目录则设为 False）

        Returns:
            压缩包路径
        """
        draft_path = Path(draft_path)
        if not draft_path.exists():
            raise FileNotFoundError(f"草稿目录不存在: {draft_path}")

        if output_zip is None:
            output_zip = str(draft_path.parent / f"{draft_path.name}.zip")

        logger.info(f"开始打包草稿: {draft_path.name}")

        # 1. 复制素材到草稿目录（可选）
        if copy_materials:
            self._copy_materials_to_draft(draft_path)

        # 2. 修改 JSON 中的路径为相对路径
        self._convert_to_relative_paths(draft_path)

        # 3. 打包成 zip
        self._create_zip(draft_path, output_zip)

        # 4. 清理原始目录（可选）
        if cleanup_original:
            shutil.rmtree(draft_path)
            logger.info(f"已删除原始草稿目录: {draft_path}")

        logger.info(f"打包完成: {output_zip}")
        return output_zip

    def _copy_materials_to_draft(self, draft_path: Path):
        """将素材文件复制到草稿目录"""
        json_path = draft_path / "draft_content.json"
        if not json_path.exists():
            raise FileNotFoundError(f"找不到 draft_content.json: {json_path}")

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 创建素材目录
        images_dir = draft_path / "images"
        audios_dir = draft_path / "audios"
        images_dir.mkdir(exist_ok=True)
        audios_dir.mkdir(exist_ok=True)

        copied_count = 0

        # 复制视频/图片素材
        if "materials" in data and "videos" in data["materials"]:
            for video in data["materials"]["videos"]:
                src_path = Path(video["path"])
                if src_path.exists():
                    dst_path = images_dir / src_path.name
                    if not dst_path.exists():
                        shutil.copy2(src_path, dst_path)
                        copied_count += 1
                        logger.debug(f"复制图片: {src_path.name}")

        # 复制音频素材
        if "materials" in data and "audios" in data["materials"]:
            for audio in data["materials"]["audios"]:
                src_path = Path(audio["path"])
                if src_path.exists():
                    dst_path = audios_dir / src_path.name
                    if not dst_path.exists():
                        shutil.copy2(src_path, dst_path)
                        copied_count += 1
                        logger.debug(f"复制音频: {src_path.name}")

        logger.info(f"复制素材完成，共 {copied_count} 个文件")

    def _convert_to_relative_paths(self, draft_path: Path):
        """将 JSON 中的绝对路径转换为相对路径"""
        json_path = draft_path / "draft_content.json"

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        converted_count = 0

        # 转换视频/图片路径
        if "materials" in data and "videos" in data["materials"]:
            for video in data["materials"]["videos"]:
                src_path = Path(video["path"])
                rel_path = f"images/{src_path.name}"
                video["path"] = rel_path
                converted_count += 1

        # 转换音频路径
        if "materials" in data and "audios" in data["materials"]:
            for audio in data["materials"]["audios"]:
                src_path = Path(audio["path"])
                rel_path = f"audios/{src_path.name}"
                audio["path"] = rel_path
                converted_count += 1

        # 保存修改后的 JSON
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"路径转换完成，共 {converted_count} 个路径")

    def _create_zip(self, draft_path: Path, output_zip: str):
        """创建压缩包"""
        output_zip = Path(output_zip)
        output_zip.parent.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zf:
            for file_path in draft_path.rglob("*"):
                if file_path.is_file():
                    arcname = file_path.relative_to(draft_path.parent)
                    zf.write(file_path, arcname)

        logger.info(f"压缩包大小: {output_zip.stat().st_size / 1024 / 1024:.2f} MB")


def unpack_draft(zip_path: str, target_dir: str) -> str:
    """
    解压草稿包

    Args:
        zip_path: 压缩包路径
        target_dir: 目标目录（剪映草稿目录）

    Returns:
        解压后的草稿路径
    """
    zip_path = Path(zip_path)
    target_dir = Path(target_dir)

    if not zip_path.exists():
        raise FileNotFoundError(f"压缩包不存在: {zip_path}")

    target_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"开始解压: {zip_path.name}")

    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(target_dir)

    # 找到草稿目录（压缩包内的第一级目录）
    draft_name = None
    for item in target_dir.iterdir():
        if item.is_dir() and (item / "draft_content.json").exists():
            draft_name = item.name
            break

    if not draft_name:
        raise ValueError("压缩包中未找到有效的草稿目录")

    draft_path = target_dir / draft_name
    logger.info(f"解压完成: {draft_path}")

    return str(draft_path)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("DraftPackager 初始化成功")
