from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
class Settings(BaseSettings):
    APP_NAME: str = "Plano de Independencia"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@db:5432/plano_independencia"
    CORS_ORIGINS: str = "http://localhost:5173"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    @property
    def cors_origins(self): return [x.strip() for x in self.CORS_ORIGINS.split(",") if x.strip()]
@lru_cache
def get_settings(): return Settings()
settings = get_settings()
