from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from app import models  # noqa: F401 — registra as tabelas no metadata
from app.db import engine
from app.models import Base
from app.routers import artefatos, chats, health, projetos

Base.metadata.create_all(bind=engine)

# ------------------------------------------------------------
# App raiz: só existe pra montar o hub sob /devian.
# O cloudflared NÃO stripa o prefixo — o backend recebe /devian/... inteiro.
# ------------------------------------------------------------
app = FastAPI(title="Devian Hub", docs_url=None, redoc_url=None, openapi_url=None)

DESCRIPTION = """
# Devian Hub API

Backend do **Devian** — o app que elimina a dependência do MacBook.

O fluxo: **app Flutter (celular) → Cloudflare (túnel `oracle-hermi`) → este backend
(Oracle) → Claude Code (container `devian`) → Postgres (`devian-db`)**.

## Autenticação

Todos os endpoints (exceto `GET /health`) exigem um **token Bearer** fixo:
`Authorization: Bearer <DEVIAN_API_TOKEN>`.

Clique em **Authorize** no topo desta página e cole o token (sem o prefixo
`Bearer `). Na fase do app, isso será substituído por **Cloudflare Access**
(login OTP por e-mail na borda, zero código de auth aqui).

## Convenções importantes

| Conceito | Regra |
|---|---|
| **Payload leve** | O app envia **só a última mensagem** (`POST /chats/{id}/mensagens`). O contexto da conversa vive na sessão do Claude Code (`--resume`) + no Postgres. Histórico **nunca** trafega. |
| **1 chat = 1 sessão** | Cada chat do app é uma sessão Claude Code com memória contínua. A primeira mensagem cria a sessão; as demais retomam pelo id. |
| **Slug automático** | O chat nasce `novo-chat` e vira o slug da primeira mensagem (ex: `qual-a-cor`). |
| **Camada por projeto** | O Claude roda com `-w /workspace/<projeto>` — carrega o `CLAUDE.md`/`.claude` do repositório e responde no contexto certo. |
| **Artefatos** | Ficam no storage local do servidor (`/home/ubuntu/devian/storage/artefatos/<projeto_id>/`). |

## Fluxo ponta-a-ponta (issue → APK)

1. Issue no GitHub → CI roda `workflow_dispatch` no repo `devian` (clona o
   projeto via chave SSH em runtime, builda o APK).
2. O hub baixa o artifact do GitHub Actions e registra em
   `GET /projetos/{id}/artefatos`.
3. O app lista/baixa o APK e o Samuel instala. 🎉

## Servidores

Use **Produção** para testar daqui do navegador (via túnel) ou **Local** se
estiver rodando o backend direto na máquina (porta 8088).
"""

OPENAPI_TAGS = [
    {
        "name": "health",
        "description": "**Público** — sem autenticação. Usado por monitoramento "
        "e pelo app para checar conectividade.",
    },
    {
        "name": "projetos",
        "description": "Projetos = repositórios de código. CRUD completo. "
        "`caminho_container` define onde o Claude roda no container (camada por projeto). "
        "Por enquanto, projetos são criados **apenas a partir de repo existente** "
        "(repo novo via template fica pra depois).",
    },
    {
        "name": "chats",
        "description": "Conversas do drawer. **1 chat = 1 sessão Claude Code** "
        "(memória contínua entre mensagens). O `name` nasce `novo-chat` e vira "
        "slug da primeira mensagem. Renomeação via `PUT /chats/{id}/rename`.",
    },
    {
        "name": "mensagens",
        "description": "Troca de mensagens com a assistente (Hermi como "
        "intermediária). O app envia **só a última mensagem** — contexto na "
        "sessão do Claude + histórico no Postgres.",
    },
    {
        "name": "artefatos",
        "description": "Arquivos gerados pelo CI (APKs, relatórios). Storage "
        "local no servidor; download direto pelo app.",
    },
]

hub = FastAPI(
    title="Devian Hub API",
    version="0.2.1",
    description=DESCRIPTION,
    contact={"name": "Samuel Gadiel", "email": "samuelgadiel@gmail.com"},
    license_info={"name": "MIT", "identifier": "MIT"},
    openapi_tags=OPENAPI_TAGS,
    swagger_ui_parameters={
        "filter": True,  # caixa de busca de endpoints
        "persistAuthorization": True,  # mantém o token entre recarregamentos
        "displayRequestDuration": True,  # mostra tempo de cada request
        "docExpansion": "list",  # já abre a lista de endpoints
        "defaultModelsExpandDepth": 3,  # detalha os schemas
    },
)


def _custom_openapi() -> dict:
    """Gera o schema OpenAPI com servidores explícitos (produção/local)."""
    if hub.openapi_schema:
        return hub.openapi_schema
    schema = get_openapi(
        title="Devian Hub API",
        version="0.2.1",
        description=DESCRIPTION,
        routes=hub.routes,
        contact={"name": "Samuel Gadiel", "email": "samuelgadiel@gmail.com"},
        license_info={"name": "MIT", "identifier": "MIT"},
        tags=OPENAPI_TAGS,
    )
    schema["servers"] = [
        {
            "url": "https://api.agapech.com.br/devian",
            "description": "Produção — via túnel Cloudflare (oracle-hermi)",
        },
        {
            "url": "/devian",
            "description": "Local — backend direto na porta 8088",
        },
    ]
    hub.openapi_schema = schema
    return schema


hub.openapi = _custom_openapi

hub.include_router(health.router)
hub.include_router(projetos.router)
hub.include_router(chats.router)
hub.include_router(artefatos.router)

app.mount("/devian", hub)
