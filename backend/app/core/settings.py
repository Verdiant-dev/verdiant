from pydantic_settings import BaseSettings, SettingsConfigDict
class Settings(BaseSettings):
    ENV: str = "dev"
    SECRET_KEY: str = "dev-change-this"
    DATABASE_URL: str = "postgresql+asyncpg://verdiant:verdiant@db:5432/verdiant"
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
settings = Settings()
