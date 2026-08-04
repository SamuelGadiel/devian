from fastapi import FastAPI

from app import models  # noqa: F401 — registra as tabelas no metadata
from app.db import engine
from app.models import Base
from app.routers import artefatos, chats, health, projetos

Base.metadata.create_all(bind=engine)

# App raiz: só existe pra montar o hub sob /devian
# (o cloudflared NÃO stripa o prefixo — o backend recebe /devian/... inteiro)
app = FastAPI(title="Devian Hub", docs_url=None, redoc_url=None)

hub = FastAPI(title="Devian Hub API", version="0.2.0")
hub.include_router(health.router)
hub.include_router(projetos.router)
hub.include_router(chats.router)
hub.include_router(artefatos.router)

app.mount("/devian", hub)
