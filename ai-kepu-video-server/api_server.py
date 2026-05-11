"""
FastAPI 应用入口
"""

import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

# 本地开发时加载 .env 文件
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(env_path)
        print(f"已加载环境变量文件: {env_path}")
    except ImportError:
        print("未安装 python-dotenv，跳过 .env 文件加载（可使用系统环境变量）")

from src.api.routes import router
from src.utils.logger import setup_logging, get_logger
from src.config import Config

# 配置日志系统
setup_logging(log_dir="logs", log_level=Config.LOG_LEVEL)
logger = get_logger(__name__)

# 创建 FastAPI 应用
app = FastAPI(
    title="InsightCut API",
    description="批量生成认知科普视频、MP4 与剪映/CapCut 草稿",
    version="1.0.0"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(router)

# 本地媒体文件路由。即使使用远端数据库，也允许无 COS 环境时回退本地文件。
# 这里按文件头识别 Content-Type，避免生图接口返回 PNG 但文件名为 .jpg 时被浏览器 ORB 拦截。
media_dir = Path(__file__).parent / "data" / "media"
media_dir.mkdir(parents=True, exist_ok=True)


def _media_type_for_file(path: Path) -> str:
    try:
        header = path.read_bytes()[:16]
    except OSError:
        header = b""

    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if header.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if header.startswith(b"RIFF") and header[8:12] == b"WEBP":
        return "image/webp"
    if header.startswith(b"RIFF") and header[8:12] == b"WAVE":
        return "audio/wav"
    if header.startswith(b"\x1aE\xdf\xa3"):
        return "video/webm"
    if len(header) >= 12 and header[4:8] == b"ftyp":
        return "video/mp4"

    suffix_map = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
        ".wav": "audio/wav",
        ".mp3": "audio/mpeg",
        ".mp4": "video/mp4",
    }
    return suffix_map.get(path.suffix.lower(), "application/octet-stream")


@app.api_route("/media/{file_path:path}", methods=["GET", "HEAD"], name="media")
async def serve_media(file_path: str):
    requested = (media_dir / file_path).resolve()
    media_root = media_dir.resolve()
    if media_root not in requested.parents and requested != media_root:
        raise HTTPException(status_code=404, detail="媒体文件不存在")
    if not requested.is_file():
        raise HTTPException(status_code=404, detail="媒体文件不存在")
    return FileResponse(
        requested,
        media_type=_media_type_for_file(requested),
        headers={
            "Cache-Control": "public, max-age=31536000, immutable",
            "Access-Control-Allow-Origin": "*",
        },
    )


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info("=" * 60)
    logger.info("InsightCut API 启动")
    logger.info(f"API 文档: http://0.0.0.0:8000/docs")
    logger.info(f"健康检查: http://0.0.0.0:8000/health")
    logger.info("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info("API 服务正在关闭...")


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "InsightCut API",
        "docs": "/docs",
        "version": "1.0.0"
    }


@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
