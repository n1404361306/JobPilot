from typing import Optional
from functools import lru_cache

from pydantic import Field, field_validator
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

class LLMProviderSettings(BaseModel):
    provider: str
    api_key: str
    base_url: str
    model: str

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = Field(default="JobPilot API", alias="APP_NAME")
    env: str = Field(default="dev", alias="ENV")
    debug: bool = Field(default=True, alias="DEBUG")
    api_v1_prefix: str = Field(default="/api", alias="API_V1_PREFIX")

    secret_key: str = Field(alias="SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=60, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_minutes: int = Field(default=10080, alias="REFRESH_TOKEN_EXPIRE_MINUTES")

    mysql_user: str = Field(default="jobpilot", alias="MYSQL_USER")
    mysql_password: str = Field(default="jobpilot", alias="MYSQL_PASSWORD")
    mysql_host: str = Field(default="127.0.0.1", alias="MYSQL_HOST")
    mysql_port: int = Field(default=3306, alias="MYSQL_PORT")
    mysql_db: str = Field(default="jobpilot", alias="MYSQL_DB")

    redis_url: str = Field(default="redis://127.0.0.1:6379/0", alias="REDIS_URL")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # ----------------LLM 配置----------------------
    # primary llm longcat
    ai_primary_provider: str = Field(default="longcat", alias="AI_PRIMARY_PROVIDER")
    ai_primary_api_key: str = Field(default="", alias="AI_PRIMARY_KEY")
    ai_primary_base_url: str = Field(default="", alias="AI_PRIMARY_BASE_URL")
    ai_primary_model: str = Field(default="", alias="AI_PRIMARY_MODEL")
    
    # fallback llm qwen
    ai_fallback_enabled: bool = Field(default=True, alias="AI_FALLBACK_ENABLED")
    ai_fallback_provider: str = Field(default="qwen", alias="AI_FALLBACK_PROVIDER")
    ai_fallback_api_key: str = Field(default="", alias="AI_FALLBACK_KEY")
    ai_fallback_base_url: str = Field(default="", alias="AI_FALLBACK_BASE_URL")
    ai_fallback_model: str = Field(default="", alias="AI_FALLBACK_MODEL")

    # llm common settings
    ai_timeout_seconds: int = Field(default=60, alias="AI_TIMEOUT_SECONDS")
    ai_temperature: float = Field(default=0.2, alias="AI_TEMPERATURE")
    ai_max_tokens: int = Field(default=4096, alias="AI_MAX_TOKENS")

    @field_validator("debug", mode="before")
    @classmethod
    def parse_debug(cls, value):
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"1", "true", "yes", "on", "debug", "dev"}:
                return True
            if normalized in {"0", "false", "no", "off", "release", "prod", "production"}:
                return False
        return value
    
    @field_validator("ai_fallback_enabled", mode="before")
    @classmethod
    def parse_ai_fallback_enabled(cls, value):
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "on"}
        return value

    @property
    def sqlalchemy_database_uri(self) -> str:
        return (
            f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_db}?charset=utf8mb4"
        )

    @property
    def ai_primary(self) -> LLMProviderSettings:
        return LLMProviderSettings(
            provider=self.ai_primary_provider,
            api_key=self.ai_primary_api_key,
            base_url=self.ai_primary_base_url.rstrip("/"),
            model=self.ai_primary_model
        )
    
    @property
    def ai_fallback(self) -> Optional[LLMProviderSettings]:
        if not self.ai_fallback_enabled or not self.ai_fallback_api_key:
            return None
        return LLMProviderSettings(
            provider=self.ai_fallback_provider,
            api_key=self.ai_fallback_api_key,
            base_url=self.ai_fallback_base_url.rstrip("/"),
            model=self.ai_fallback_model
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
