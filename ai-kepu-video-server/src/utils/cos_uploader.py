"""
腾讯云 COS 上传工具
本地开发模式下自动切换为 LocalUploader
"""

import logging
import os
from pathlib import Path
from typing import Optional

from src.config import Config

logger = logging.getLogger(__name__)


def COSUploader(**kwargs):
    """工厂函数：优先远端 COS，缺少配置时自动回退本地存储。"""
    use_remote_storage = os.environ.get("USE_REMOTE_DB") == "1" and all([
        kwargs.get("secret_id") or Config.COS_SECRET_ID,
        kwargs.get("secret_key") or Config.COS_SECRET_KEY,
        kwargs.get("bucket") or Config.COS_BUCKET,
    ])

    if use_remote_storage:
        try:
            return _COSUploader(**kwargs)
        except Exception as e:
            logger.warning(f"COS 初始化失败，回退到本地存储: {e}")

    from src.utils.local_uploader import LocalUploader
    return LocalUploader(**kwargs)


class _COSUploader:
    """腾讯云 COS 上传器"""

    def __init__(
        self,
        secret_id: Optional[str] = None,
        secret_key: Optional[str] = None,
        region: Optional[str] = None,
        bucket: Optional[str] = None,
        bucket_dir: Optional[str] = None,
        cdn_domain: Optional[str] = None,
    ):
        """
        初始化 COS 上传器

        Args:
            secret_id: 腾讯云 SecretId（默认从 Config 读取）
            secret_key: 腾讯云 SecretKey（默认从 Config 读取）
            region: COS 地域（默认从 Config 读取）
            bucket: COS 存储桶名称（默认从 Config 读取）
            bucket_dir: COS 存储目录前缀（默认从 Config 读取）
            cdn_domain: CDN 加速域名（默认从 Config 读取）
        """
        self.secret_id = secret_id or Config.COS_SECRET_ID
        self.secret_key = secret_key or Config.COS_SECRET_KEY
        self.region = region or Config.COS_REGION
        self.bucket = bucket or Config.COS_BUCKET
        self.bucket_dir = bucket_dir or Config.COS_BUCKET_DIR
        self.cdn_domain = cdn_domain or Config.COS_CDN_DOMAIN

        if not all([self.secret_id, self.secret_key, self.bucket]):
            raise ValueError(
                "缺少 COS 配置，请设置环境变量：\n"
                "  COS_SECRET_ID\n"
                "  COS_SECRET_KEY\n"
                "  COS_BUCKET\n"
                "  COS_REGION (可选，默认 ap-guangzhou)"
            )

        # 延迟导入，避免未安装 cos-python-sdk-v5 时报错
        try:
            from qcloud_cos import CosConfig, CosS3Client
        except ImportError:
            raise ImportError(
                "请先安装腾讯云 COS SDK：pip install cos-python-sdk-v5"
            )

        config = CosConfig(
            Region=self.region,
            SecretId=self.secret_id,
            SecretKey=self.secret_key,
        )
        self.client = CosS3Client(config)

    def upload(
        self,
        file_path: str,
        cos_path: Optional[str] = None,
        enable_md5: bool = False,
    ) -> str:
        """
        上传文件到 COS

        Args:
            file_path: 本地文件路径
            cos_path: COS 对象路径（默认使用 草稿名称/文件名 格式）
            enable_md5: 是否启用 MD5 校验

        Returns:
            文件的访问 URL
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        # 默认使用 草稿名称/文件名 格式
        # 例如：穷查理宝典/穷查理宝典.zip
        if cos_path is None:
            # 从文件名提取草稿名称（去掉 .zip 后缀）
            draft_name = file_path.stem
            cos_path = f"{draft_name}/{file_path.name}"

        # 添加目录前缀
        if self.bucket_dir:
            cos_path = f"{self.bucket_dir}/{cos_path}"

        logger.info(f"上传文件: {file_path.name} -> {cos_path}")

        try:
            response = self.client.upload_file(
                Bucket=self.bucket,
                LocalFilePath=str(file_path),
                Key=cos_path,
                EnableMD5=enable_md5,
            )

            # 构建访问 URL - 优先使用 CDN 域名
            if self.cdn_domain:
                url = f"https://{self.cdn_domain}/{cos_path}"
            else:
                url = f"https://{self.bucket}.cos.{self.region}.myqcloud.com/{cos_path}"
            logger.info(f"上传成功: {url}")
            return url

        except Exception as e:
            logger.error(f"上传失败: {e}")
            raise

    def upload_with_progress(
        self,
        file_path: str,
        cos_path: Optional[str] = None,
    ) -> str:
        """
        上传文件到 COS（带进度条）

        Args:
            file_path: 本地文件路径
            cos_path: COS 对象路径（默认使用 草稿名称/文件名 格式）

        Returns:
            文件的访问 URL
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        # 默认使用 草稿名称/文件名 格式
        if cos_path is None:
            draft_name = file_path.stem
            cos_path = f"{draft_name}/{file_path.name}"

        # 添加目录前缀
        if self.bucket_dir:
            cos_path = f"{self.bucket_dir}/{cos_path}"

        logger.info(f"上传文件: {file_path.name} -> {cos_path}")

        def progress_callback(consumed_bytes, total_bytes):
            if total_bytes:
                percent = int(100 * consumed_bytes / total_bytes)
                logger.info(f"上传进度: {percent}% ({consumed_bytes}/{total_bytes} bytes)")

        try:
            response = self.client.upload_file(
                Bucket=self.bucket,
                LocalFilePath=str(file_path),
                Key=cos_path,
                progress_callback=progress_callback,
            )

            # 构建访问 URL - 优先使用 CDN 域名
            if self.cdn_domain:
                url = f"https://{self.cdn_domain}/{cos_path}"
            else:
                url = f"https://{self.bucket}.cos.{self.region}.myqcloud.com/{cos_path}"
            logger.info(f"上传成功: {url}")
            return url

        except Exception as e:
            logger.error(f"上传失败: {e}")
            raise


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("COSUploader 初始化成功")
    print("\n环境变量配置：")
    print(f"  COS_SECRET_ID: {'已设置' if os.getenv('COS_SECRET_ID') else '未设置'}")
    print(f"  COS_SECRET_KEY: {'已设置' if os.getenv('COS_SECRET_KEY') else '未设置'}")
    print(f"  COS_REGION: {os.getenv('COS_REGION', 'ap-guangzhou')}")
    print(f"  COS_BUCKET: {os.getenv('COS_BUCKET', '未设置')}")
    print(f"  COS_BUCKET_DIR: {os.getenv('COS_BUCKET_DIR', '未设置')}")
    print(f"  COS_CDN_DOMAIN: {os.getenv('COS_CDN_DOMAIN', '未设置')}")
