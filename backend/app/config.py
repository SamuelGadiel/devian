from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuração via env vars com prefixo DEVIAN_ (ver .env.example)."""

    api_token: str = "troque-me"
    database_url: str = "postgresql+psycopg2://devian:devian@127.0.0.1:5434/devian"
    container_devian: str = "devian"
    claude_cmd: str = "claude"
    claude_timeout: int = 300
    storage_dir: str = "/home/ubuntu/devian/storage"

    # Auth (login com Google)
    google_client_id: str = ""  # OAuth Client ID (Web) do Google Cloud Console
    session_jwt_secret: str = "troque-me"  # openssl rand -hex 32
    session_ttl_days: int = 30
    allowed_login_emails: str = (
        ""  # CSV de e-mails autorizados a entrar (vazio = só o 1º login/admin)
    )

    model_config = {"env_file": ".env", "env_prefix": "DEVIAN_", "extra": "ignore"}


settings = Settings()
