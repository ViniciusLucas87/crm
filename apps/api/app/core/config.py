from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    pns_env: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/pns_crm"
    redis_url: str = "redis://:redis_dev@localhost:6379/0"
    redis_password: str = "redis_dev"
    allowed_origins: str = "http://localhost:3000"
    clerk_issuer: str | None = None
    clerk_jwks_url: str | None = None
    crm_allowed_user_ids: str = ""
    crm_default_organization_slug: str = "pacific-north-systems"
    deepseek_api_key: str = ""
    deepseek_api_base: str = "https://api.deepseek.com/v1"
    deepseek_model: str = "deepseek-chat"

    @property
    def allowed_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]

    @property
    def crm_allowed_user_id_set(self) -> set[str]:
        return {value.strip() for value in self.crm_allowed_user_ids.split(",") if value.strip()}


@lru_cache
def get_settings() -> Settings:
    return Settings()
