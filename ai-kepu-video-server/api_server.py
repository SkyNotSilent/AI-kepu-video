"""
FastAPI 应用入口
"""

import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from src.api.routes import router
from src.utils.logger import setup_logging, get_logger
from src.config import Config

# 本地开发时加载 .env 文件
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(env_path)
        print(f"已加载环境变量文件: {env_path}")
    except ImportError:
        print("未安装 python-dotenv，跳过 .env 文件加载（可使用系统环境变量）")

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

# 本地开发模式：挂载媒体文件静态路由
if os.environ.get("USE_REMOTE_DB") != "1":
    media_dir = Path(__file__).parent / "data" / "media"
    media_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/media", StaticFiles(directory=str(media_dir)), name="media")


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
