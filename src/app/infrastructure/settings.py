"""Application settings."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-backed settings for infrastructure components."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "Covenant Engine"
    database_url: str = Field(default="postgresql://postgres:postgres@postgres:5432/covenants")
    publish_mode: str = "smart_contract"
    rpc_url: str = "http://anvil:8545"
    chain_id: int = 31337
    deployer_private_key: str = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
    contract_address: str = ""


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
