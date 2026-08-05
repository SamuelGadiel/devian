from pathlib import Path

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app import models  # noqa: F401 — registra as tabelas no metadata
from app.db import engine
from app.models import Base
from app.routers import artifacts, chats, health, projects

Base.metadata.create_all(bind=engine)

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

# ------------------------------------------------------------
# App raiz: só existe pra montar o hub sob /devian.
# O cloudflared NÃO stripa o prefixo — o backend recebe /devian/... inteiro.
# ------------------------------------------------------------
app = FastAPI(title="Devian Hub", docs_url=None, redoc_url=None, openapi_url=None)

DESCRIPTION = """
API do hub do **Devian** — projetos, chats (Claude Code) e artefatos de build.

**Autenticação:** todos os endpoints exigem um **Bearer token** (`DEVIAN_API_TOKEN`).
Clique em **Authorize** e cole o token, sem o prefixo `Bearer `.
Exceção: `GET /health`, que é público.
"""

OPENAPI_TAGS = [
    {
        "name": "health",
        "description": "**Público** — sem autenticação. Usado por monitoramento "
        "e pelo app para checar conectividade.",
    },
    {
        "name": "projects",
        "description": "Projetos = repositórios de código. CRUD completo. "
        "`container_path` define onde o Claude roda no container (camada por "
        "projeto). Projetos são criados apenas a partir de repo existente.",
    },
    {
        "name": "chats",
        "description": "Conversas do drawer. **1 chat = 1 sessão Claude Code** "
        "(memória contínua entre mensagens). O `name` nasce `new-chat` e vira "
        "slug da primeira mensagem. Renomeação via `PUT /chats/{id}/rename`.",
    },
    {
        "name": "artifacts",
        "description": "Arquivos gerados pelo CI (APKs, relatórios). "
        "Storage local no servidor; download direto pelo app.",
    },
]

hub = FastAPI(
    title="Devian Hub API",
    version="0.3.0",
    description=DESCRIPTION,
    openapi_tags=OPENAPI_TAGS,
    docs_url=None,   # /swagger é servido manualmente (Swagger UI 4.x clássica)
    redoc_url=None,  # sem ReDoc
)


def _custom_openapi() -> dict:
    """OpenAPI 3.0.x (a UI v4 não renderiza 3.1) com servidores explícitos."""
    if hub.openapi_schema:
        return hub.openapi_schema
    schema = get_openapi(
        title="Devian Hub API",
        version="0.3.0",
        openapi_version="3.0.3",
        description=DESCRIPTION,
        routes=hub.routes,
        tags=OPENAPI_TAGS,
        servers=[
            {
                "url": "https://api.agapech.com.br/devian",
                "description": "Produção — via túnel Cloudflare (oracle-hermi)",
            },
            {
                "url": "/devian",
                "description": "Local — backend direto na porta 8088",
            },
        ],
    )
    hub.openapi_schema = schema
    return schema


hub.openapi = _custom_openapi

SWAGGER_HTML = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <title>Devian Hub API — Swagger</title>
  <link rel="stylesheet" href="/devian/static/swagger/swagger-ui.css">
  <link rel="icon" type="image/png" href="/devian/static/swagger/favicon-32x32.png">
  <style>
    html { box-sizing: border-box; overflow-y: scroll; }
    *, *:before, *:after { box-sizing: inherit; }
    body { margin: 0; background: #fafafa; }
  </style>
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="/devian/static/swagger/swagger-ui-bundle.js"></script>
  <script src="/devian/static/swagger/swagger-ui-standalone-preset.js"></script>
  <script>
    window.onload = function () {
      window.ui = SwaggerUIBundle({
        urls: [{ url: "/devian/openapi.json", name: "Devian Hub API" }],
        dom_id: "#swagger-ui",
        deepLinking: true,
        presets: [
          SwaggerUIBundle.presets.apis,
          SwaggerUIStandalonePreset
        ],
        layout: "StandaloneLayout",
        persistAuthorization: true,
        displayRequestDuration: true
      });
    };
  </script>
</body>
</html>
"""


@hub.get("/swagger", include_in_schema=False)
def swagger_ui() -> HTMLResponse:
    """Swagger UI clássica (v4.x), assets servidos localmente — sem CDN."""
    return HTMLResponse(SWAGGER_HTML)


hub.include_router(health.router)
hub.include_router(projects.router)
hub.include_router(chats.router)
hub.include_router(artifacts.router)

# Estáticos do Swagger servidos localmente. Montar ANTES do hub:
# /devian/static/* precisa ganhar do mount genérico /devian.
app.mount("/devian/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount("/devian", hub)
