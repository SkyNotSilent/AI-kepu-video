"""
配置管理模块
"""
import json
import os
from copy import deepcopy
from pathlib import Path


def _load_local_env() -> None:
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if not env_path.exists():
        return
    try:
        from dotenv import load_dotenv
    except ImportError:
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip("'\""))
        return
    load_dotenv(env_path)


_load_local_env()


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default)


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


def _clamp_int(value, default: int, minimum: int, maximum: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = default
    return max(minimum, min(maximum, parsed))


class Config:
    """配置类 - 默认配置 + data/config.json 运行时覆盖"""

    BASE_DIR: Path = Path(__file__).resolve().parent.parent

    # LLM 配置。真实 key 请写入 .env、环境变量，或通过前端“模型配置”页保存到 data/config.json。
    LLM_API_KEY: str = _env("LLM_API_KEY", "")
    LLM_BASE_URL: str = _env("LLM_BASE_URL", "")
    LLM_MODEL: str = _env("LLM_MODEL", "")
    LLM_PROTOCOL: str = _env("LLM_PROTOCOL", "openai")

    # 旧版 Anthropic 命名仍保留为回退，避免已有部署升级后配置失效。
    ANTHROPIC_API_KEY: str = _env("ANTHROPIC_API_KEY", _env("ANTHROPIC_AUTH_TOKEN", ""))
    ANTHROPIC_BASE_URL: str = _env("ANTHROPIC_BASE_URL", "https://api.anthropic.com")
    ANTHROPIC_MODEL: str = _env("ANTHROPIC_MODEL", "claude-sonnet-4-5")

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

    CONFIG_FILE: Path = BASE_DIR / "data" / "config.json"
    LEGACY_CONFIG_FILE: Path = Path("data/config.json")

    @classmethod
    def default_model_config(cls) -> dict:
        return {
            "llm": {
                "base_url": cls.LLM_BASE_URL or cls.ANTHROPIC_BASE_URL,
                "api_key": cls.LLM_API_KEY or cls.ANTHROPIC_API_KEY,
                "model": cls.LLM_MODEL or cls.ANTHROPIC_MODEL,
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
            "generation": {
                "tts_concurrency": _clamp_int(_env("TTS_CONCURRENCY", "1"), 1, 1, 8),
                "image_concurrency": _clamp_int(_env("IMAGE_CONCURRENCY", "1"), 1, 1, 8),
            },
        }

    @classmethod
    def load_model_config(cls) -> dict:
        config = deepcopy(cls.default_model_config())
        config_file = cls._resolve_config_file()
        if not config_file.exists():
            cls._normalize_model_config(config)
            return config

        try:
            with config_file.open("r", encoding="utf-8") as f:
                overrides = json.load(f)
        except Exception:
            cls._normalize_model_config(config)
            return config

        for section in ("llm", "image", "tts", "generation"):
            if isinstance(overrides.get(section), dict):
                config[section].update({
                    key: value
                    for key, value in overrides[section].items()
                    if value is not None
                })
        cls._normalize_model_config(config)
        return config

    @classmethod
    def save_model_config(cls, config: dict) -> dict:
        current = cls.load_model_config()
        incoming = config or {}

        for section in ("llm", "image", "tts", "generation"):
            if isinstance(incoming.get(section), dict):
                current[section].update({
                    key: value
                    for key, value in incoming[section].items()
                    if value is not None
                })
        cls._normalize_model_config(current)

        cls.CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with cls.CONFIG_FILE.open("w", encoding="utf-8") as f:
            json.dump(current, f, ensure_ascii=False, indent=2)
        return current

    @classmethod
    def _normalize_generation_config(cls, config: dict) -> None:
        generation = config.setdefault("generation", {})
        generation["tts_concurrency"] = _clamp_int(
            generation.get("tts_concurrency"), 1, 1, 8
        )
        generation["image_concurrency"] = _clamp_int(
            generation.get("image_concurrency"), 1, 1, 8
        )

    @classmethod
    def _normalize_tts_config(cls, config: dict) -> None:
        tts = config.setdefault("tts", {})
        tts["api_url"] = (
            tts.get("api_url")
            or tts.get("url")
            or tts.get("base_url")
            or cls.DOUBAO_TTS_API_URL
        )
        tts["appid"] = (
            tts.get("appid")
            or tts.get("app_id")
            or tts.get("appId")
            or cls.DOUBAO_TTS_APPID
        )
        tts["token"] = (
            tts.get("token")
            or tts.get("access_token")
            or tts.get("accessToken")
            or tts.get("api_key")
            or cls.DOUBAO_TTS_TOKEN
        )
        tts["cluster"] = tts.get("cluster") or cls.DOUBAO_TTS_CLUSTER
        tts["default_voice"] = (
            tts.get("default_voice")
            or tts.get("voice_type")
            or tts.get("voice")
            or cls.DOUBAO_TTS_DEFAULT_VOICE
        )

    @classmethod
    def _normalize_model_config(cls, config: dict) -> None:
        cls._normalize_tts_config(config)
        cls._normalize_generation_config(config)

    @classmethod
    def _resolve_config_file(cls) -> Path:
        if cls.CONFIG_FILE.exists():
            return cls.CONFIG_FILE

        legacy = cls.LEGACY_CONFIG_FILE
        try:
            legacy = legacy.resolve()
        except Exception:
            pass

        if legacy != cls.CONFIG_FILE and legacy.exists():
            return legacy
        return cls.CONFIG_FILE

    @classmethod
    def llm_config(cls) -> dict:
        return cls.load_model_config()["llm"]

    @classmethod
    def image_config(cls) -> dict:
        return cls.load_model_config()["image"]

    @classmethod
    def tts_config(cls) -> dict:
        return cls.load_model_config()["tts"]

    @classmethod
    def generation_config(cls) -> dict:
        return cls.load_model_config()["generation"]
