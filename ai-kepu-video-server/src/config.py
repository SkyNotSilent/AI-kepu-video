"""
配置管理模块
"""
import json
import os
from copy import deepcopy
from pathlib import Path


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default)


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


class Config:
    """配置类 - 默认配置 + data/config.json 运行时覆盖"""

    # LLM 配置。真实 key 请写入 .env、环境变量，或通过前端“模型配置”页保存到 data/config.json。
    ANTHROPIC_API_KEY: str = _env("ANTHROPIC_API_KEY", _env("ANTHROPIC_AUTH_TOKEN", ""))
    ANTHROPIC_BASE_URL: str = _env("ANTHROPIC_BASE_URL", "https://api.anthropic.com")
    ANTHROPIC_MODEL: str = _env("ANTHROPIC_MODEL", "claude-sonnet-4-5")
    LLM_PROTOCOL: str = _env("LLM_PROTOCOL", "anthropic")

    # 豆包 TTS 配置
    DOUBAO_TTS_API_URL: str = _env("DOUBAO_TTS_API_URL", "https://openspeech.bytedance.com/api/v1/tts")
    DOUBAO_TTS_APPID: str = _env("DOUBAO_TTS_APPID", "")
    DOUBAO_TTS_TOKEN: str = _env("DOUBAO_TTS_TOKEN", "")
    DOUBAO_TTS_CLUSTER: str = _env("DOUBAO_TTS_CLUSTER", "volcano_tts")
    DOUBAO_TTS_DEFAULT_VOICE: str = _env("DOUBAO_TTS_DEFAULT_VOICE", "zh_male_jieshuoxiaoming_moon_bigtts")

    # 图像生成配置
    SEEDREAM_API_KEY: str = _env("SEEDREAM_API_KEY", "")
    SEEDREAM_API_URL: str = _env("SEEDREAM_API_URL", "https://api.openai.com/v1/images/generations")
    SEEDREAM_MODEL: str = _env("SEEDREAM_MODEL", "gpt-image-1")

    # 腾讯云 COS 配置
    COS_SECRET_ID: str = _env("COS_SECRET_ID", "")
    COS_SECRET_KEY: str = _env("COS_SECRET_KEY", "")
    COS_REGION: str = _env("COS_REGION", "ap-guangzhou")
    COS_BUCKET: str = _env("COS_BUCKET", "")
    COS_BUCKET_DIR: str = _env("COS_BUCKET_DIR", "kepu")
    COS_CDN_DOMAIN: str = _env("COS_CDN_DOMAIN", "")

    # MySQL 配置
    MYSQL_HOST: str = _env("MYSQL_HOST", "127.0.0.1")
    MYSQL_PORT: int = _env_int("MYSQL_PORT", 3306)
    MYSQL_USER: str = _env("MYSQL_USER", "root")
    MYSQL_PASSWORD: str = _env("MYSQL_PASSWORD", "")
    MYSQL_DATABASE: str = _env("MYSQL_DATABASE", "ai_kepu")

    # Redis 配置
    REDIS_HOST: str = _env("REDIS_HOST", "127.0.0.1")
    REDIS_PORT: int = _env_int("REDIS_PORT", 6379)
    REDIS_DB: int = _env_int("REDIS_DB", 0)
    REDIS_PASSWORD: str = _env("REDIS_PASSWORD", "")

    # 日志配置
    LOG_LEVEL: str = _env("LOG_LEVEL", "DEBUG")

    CONFIG_FILE: Path = Path("data/config.json")

    @classmethod
    def default_model_config(cls) -> dict:
        return {
            "llm": {
                "base_url": cls.ANTHROPIC_BASE_URL,
                "api_key": cls.ANTHROPIC_API_KEY,
                "model": cls.ANTHROPIC_MODEL,
                "protocol": cls.LLM_PROTOCOL,
            },
            "image": {
                "api_url": cls.SEEDREAM_API_URL,
                "api_key": cls.SEEDREAM_API_KEY,
                "model": cls.SEEDREAM_MODEL,
                "size": _env("SEEDREAM_SIZE", "auto"),
            },
            "tts": {
                "api_url": cls.DOUBAO_TTS_API_URL,
                "appid": cls.DOUBAO_TTS_APPID,
                "token": cls.DOUBAO_TTS_TOKEN,
                "cluster": cls.DOUBAO_TTS_CLUSTER,
                "default_voice": cls.DOUBAO_TTS_DEFAULT_VOICE,
            },
        }

    @classmethod
    def load_model_config(cls) -> dict:
        config = deepcopy(cls.default_model_config())
        if not cls.CONFIG_FILE.exists():
            return config

        try:
            with cls.CONFIG_FILE.open("r", encoding="utf-8") as f:
                overrides = json.load(f)
        except Exception:
            return config

        for section in ("llm", "image", "tts"):
            if isinstance(overrides.get(section), dict):
                config[section].update({
                    key: value
                    for key, value in overrides[section].items()
                    if value is not None
                })
        return config

    @classmethod
    def save_model_config(cls, config: dict) -> dict:
        current = cls.load_model_config()
        incoming = config or {}

        for section in ("llm", "image", "tts"):
            if isinstance(incoming.get(section), dict):
                current[section].update({
                    key: value
                    for key, value in incoming[section].items()
                    if value is not None
                })

        cls.CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with cls.CONFIG_FILE.open("w", encoding="utf-8") as f:
            json.dump(current, f, ensure_ascii=False, indent=2)
        return current

    @classmethod
    def llm_config(cls) -> dict:
        return cls.load_model_config()["llm"]

    @classmethod
    def image_config(cls) -> dict:
        return cls.load_model_config()["image"]

    @classmethod
    def tts_config(cls) -> dict:
        return cls.load_model_config()["tts"]
