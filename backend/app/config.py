from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuração via env vars com prefixo DEVIAN_ (ver .env.example)."""

    api_token: str = "troque-me"
    database_url: str = "postgresql+psycopg2://devian:devian@127.0.0.1:5434/devian"
    container_devian: str = "devian"
    claude_cmd: str = "claude"
    claude_timeout: int = 300

    model_config = {"env_file": ".env", "env_prefix": "DEVIAN_", "extra": "ignore"}


settings = Settings()
