from pydantic import computed_field
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Базовые параметры окружения
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    # Параметры подключения к PostgreSQL
    POSTGRES_USER: str = "tradepulse"
    POSTGRES_PASSWORD: str = "tradepulse_password"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "tradepulse_db"
# Параметры пула соединений
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30
    DB_ECHO: bool = False

    @computed_field  # type: ignore[prop-decorator]
    @property
    def database_url(self) -> str:
        """Динамически формирует валидную строку подключения postgresql+asyncpg."""
        return str(
            MultiHostUrl.build(
                scheme="postgresql+asyncpg",
                username=self.POSTGRES_USER,
                password=self.POSTGRES_PASSWORD,
                host=self.POSTGRES_HOST,
                port=self.POSTGRES_PORT,
                path=self.POSTGRES_DB,
            )
        )

settings = Settings()
