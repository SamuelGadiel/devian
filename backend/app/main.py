from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app import models  # noqa: F401 — registra as tabelas no metadata
from app.db import engine
from app.models import Base
from app.routers import artifacts, chats, health, messages, projects

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
    {"name": "Projects"},
    {"name": "Chats"},
    {"name": "Messages"},
    {"name": "Artifacts"},
    {"name": "Health"},
]

hub = FastAPI(
    title="Devian Hub API",
    version="0.5.0",
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
        version="0.5.0",
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
hub.include_router(messages.router)
hub.include_router(artifacts.router)


# ------------------------------------------------------------
# Erros: TODOS respondem {"message": "..."} (padrão do hub)
# ------------------------------------------------------------
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail},
        headers=exc.headers,
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    errors = []
    for err in exc.errors():
        loc = [str(x) for x in err.get("loc", []) if x != "body"]
        errors.append(
            {
                "field": ".".join(loc) if loc else None,
                "message": err.get("msg"),
            }
        )
    return JSONResponse(
        status_code=422,
        content={"message": "Corpo da requisição inválido", "errors": errors},
    )


async def not_found_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """404 de rota inexistente — levantado com a classe base do Starlette."""
    detail = exc.detail if isinstance(exc.detail, str) else "Rota não encontrada"
    message = "Rota não encontrada" if detail == "Not Found" else detail
    return JSONResponse(status_code=404, content={"message": message})


# Registra nos DOIS apps: o 404 de rota inexistente é levantado pelo app raiz,
# os erros de negócio pelo hub montado em /devian.
for _app in (app, hub):
    _app.add_exception_handler(HTTPException, http_exception_handler)
    _app.add_exception_handler(RequestValidationError, validation_exception_handler)
    _app.add_exception_handler(404, not_found_handler)

# Estáticos do Swagger servidos localmente. Montar ANTES do hub:
# /devian/static/* precisa ganhar do mount genérico /devian.
app.mount("/devian/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount("/devian", hub)
