from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuração via env vars com prefixo DEVIAN_ (ver .env.example)."""

    database_url: str = "postgresql+psycopg2://devian:devian@127.0.0.1:5434/devian"
    container_devian: str = "devian"
    claude_cmd: str = "claude"
    claude_timeout: int = 300
    storage_dir: str = "/home/ubuntu/devian/storage"

    # Auth (e-mail + senha — o backend cuida do auth)
    session_jwt_secret: str = "troque-me"  # openssl rand -hex 32
    access_token_ttl_minutes: int = 60  # JWT de acesso (vai no Bearer)
    refresh_token_ttl_days: int = 90  # refresh token opaco (rotacionado)

    model_config = {"env_file": ".env", "env_prefix": "DEVIAN_", "extra": "ignore"}


settings = Settings()
