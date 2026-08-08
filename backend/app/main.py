from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app import models  # noqa: F401 — registra as tabelas no metadata
from app.db import engine
from app.models import Base
from app.routers import artifacts, auth, chats, health, messages, projects, users

Base.metadata.create_all(bind=engine)

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

# ------------------------------------------------------------
# App raiz: só existe pra montar o hub sob /devian.
# O cloudflared NÃO stripa o prefixo — o backend recebe /devian/... inteiro.
# ------------------------------------------------------------
app = FastAPI(title="Devian Hub", docs_url=None, redoc_url=None, openapi_url=None)

DESCRIPTION = """
API do hub do **Devian** — projetos, chats (Claude Code) e artefatos de build.

**Autenticação:** endpoints protegidos exigem um **access token** (JWT)
enviado como `Authorization: Bearer <token>`.

1. `POST /auth/login` com **e-mail + senha** devolve o par
   `{access_token, refresh_token}`.
2. O `access_token` (curto) autentica as chamadas.
3. Quando ele expirar, `POST /auth/refresh` com o `refresh_token` devolve um
   par novo (o token antigo é revogado — rotação).
4. `POST /auth/logout` revoga o refresh token e encerra a sessão.

Os dados (projetos, chats, mensagens e artefatos) são escopados pelo usuário
autenticado: cada usuário vê apenas os próprios dados, resolvidos
automaticamente a partir do token.

Endpoints públicos: `GET /health`, `POST /auth/login` e `POST /auth/refresh`.
Clique em **Authorize** e cole o `access_token`, sem o prefixo `Bearer `.
"""

OPENAPI_TAGS = [
    {"name": "Auth"},
    {"name": "Users"},
    {"name": "Projects"},
    {"name": "Chats"},
    {"name": "Messages"},
    {"name": "Artifacts"},
    {"name": "Health"},
]

hub = FastAPI(
    title="Devian Hub API",
    version="0.7.0",
    description=DESCRIPTION,
    openapi_tags=OPENAPI_TAGS,
    docs_url=None,   # /swagger é servido manualmente (Swagger UI 4.x clássica)
    redoc_url=None,  # sem ReDoc
)


def _downgrade_examples(node):
    """OpenAPI 3.0: Schema Object aceita `example` (singular), não `examples`
    (plural — só existe em 3.1 / media types). Converte recursivamente,
    preservando o primeiro exemplo."""
    if isinstance(node, dict):
        if "examples" in node and isinstance(node["examples"], list):
            examples = node["examples"]
            if examples:
                node["example"] = examples[0]
            node.pop("examples", None)
        for value in node.values():
            _downgrade_examples(value)
    elif isinstance(node, list):
        for item in node:
            _downgrade_examples(item)
    return node


def _fix_nullable(node):
    """Converte `anyOf: [T, {type: null}]` (gerado pelo Pydantic p/ campos
    `X | None`) em `type: T, nullable: true` — o validador oficial do Swagger
    (validator.swagger.io) rejeita `{type: null}` dentro de anyOf em Schema
    Objects; `nullable: true` é o jeito canônico do OpenAPI 3.0."""
    if isinstance(node, dict):
        any_of = node.get("anyOf")
        if isinstance(any_of, list) and len(any_of) == 2:
            if any(m == {"type": "null"} for m in any_of):
                real = [m for m in any_of if m != {"type": "null"}][0]
                for key, value in real.items():
                    node.setdefault(key, value)
                node["nullable"] = True
                node.pop("anyOf", None)
        for value in list(node.values()):
            _fix_nullable(value)
    elif isinstance(node, list):
        for item in node:
            _fix_nullable(item)
    return node


def _custom_openapi() -> dict:
    """OpenAPI 3.0.x (a UI v4 não renderiza 3.1) com servidores explícitos."""
    if hub.openapi_schema:
        return hub.openapi_schema
    schema = get_openapi(
        title="Devian Hub API",
        version="0.7.0",
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
    # Remove `examples` (inválido em 3.0) e converte anyOf+null em nullable
    # antes de servir — senão o validator.swagger.io marca o doc como INVALID.
    schema = _downgrade_examples(schema)
    schema = _fix_nullable(schema)
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
hub.include_router(auth.router)
hub.include_router(users.router)
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
