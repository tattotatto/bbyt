from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    APP_NAME: str = "HXMall B2B API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/hxmall"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT
    JWT_SECRET_KEY: str = "change-me-in-production-use-a-real-secret"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # OSS / File Storage
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 10
    OSS_ENDPOINT: str = ""
    OSS_ACCESS_KEY: str = ""
    OSS_SECRET_KEY: str = ""
    OSS_BUCKET: str = ""

    # WeChat
    WECHAT_APPID: str = ""
    WECHAT_SECRET: str = ""

    # AI / LLM — 对话下单引擎 + 向量检索
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/v1"
    DEEPSEEK_MODEL: str = "deepseek-chat"
    AI_DEFAULT_MODEL: str = "deepseek"  # deepseek | qwen（Phase 3）
    AI_MAX_TOKENS: int = 2048
    AI_TEMPERATURE: float = 0.7
    # Qwen / 千问 (Phase 3)
    QWEN_API_KEY: str = ""
    QWEN_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    QWEN_MODEL: str = "qwen-max"

    # Embedding — 知识库向量化
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_API_KEY: str = ""
    EMBEDDING_BASE_URL: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()
