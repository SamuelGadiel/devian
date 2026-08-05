# Devian Hub API

Backend do Devian — conecta o app Flutter ao Claude Code (container `devian`, Oracle).
Exposto via túnel Cloudflare `oracle-hermi`: `https://api.agapech.com.br/devian`.

## Stack
- **FastAPI** (Python 3.11) montado em `/devian` (cloudflared não stripa prefixo)
- **PostgreSQL 16** — container `devian-db` (127.0.0.1:5434, rede `devian-net`)
- **Claude Code** — `docker exec devian claude -p` (headless, workdir = pasta do projeto)
- **Storage local** — `/home/ubuntu/devian/storage/artifacts/<project_id>/`

## Endpoints (todos sob `/devian`, exceto `/health` exigem Bearer token)

### Projects
| Método | Rota | Descrição |
|---|---|---|
| GET | `/projects` | Lista projetos |
| POST | `/projects` | Cria projeto (name, repo_url, default_branch, container_path) |
| GET | `/projects/{project_id}` | Detalhe |
| PUT | `/projects/{project_id}` | Atualiza (name, repo_url, default_branch, container_path) |
| DELETE | `/projects/{project_id}` | Deleta (cascata: chats, messages, artifacts) |

### Chats (1 chat = 1 sessão Claude)
| Método | Rota | Descrição |
|---|---|---|
| GET | `/chats?project_id=N` | Lista chats (recentes primeiro) |
| POST | `/chats` | Cria chat `{project_id, name?}` |
| GET | `/chats/{chat_id}` | Detalhe |
| DELETE | `/chats/{chat_id}` | Deleta chat + histórico |
| PUT | `/chats/{chat_id}/rename` | Renomeia `{name}` |
| GET | `/chats/{chat_id}/messages?cursor=&limit=` | Histórico paginado (cursor-based) |
| POST | `/chats/{chat_id}/messages` | Envia msg `{content}` — app manda SÓ a última msg |

### Artifacts (storage no servidor)
| Método | Rota | Descrição |
|---|---|---|
| GET | `/projects/{project_id}/artifacts` | Lista artifacts |
| GET | `/projects/{project_id}/artifacts/{artifact_id}` | Download |

## Regras de negócio
- **Payload leve**: o app envia só a última mensagem. Contexto = sessão Claude no container (--resume) + histórico no Postgres.
- **1 chat = 1 sessão**: primeira msg cria sessão (--session-id), demais retomam (--resume <id>).
- **Slug do chat**: name default "new-chat" vira slug da 1ª mensagem (ex: "qual-a-cor").
- **Camada por projeto**: Claude roda com `-w /workspace/<projeto>` → carrega CLAUDE.md/.claude.
- **API em inglês**: endpoints, parâmetros, payloads e responses em inglês; só textos exibidos ao usuário final ficam em português.

## Rodar
```bash
cd backend
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env   # DEVIAN_API_TOKEN, DATABASE_URL, STORAGE_DIR
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8088
```
Produção: systemd `devian-backend.service` (porta 8088; 8080 = SearXNG).

## Documentação (Swagger)

- **Swagger UI**: https://api.agapech.com.br/devian/swagger
- **OpenAPI JSON**: https://api.agapech.com.br/devian/openapi.json (snapshot versionado em `docs/openapi.json`)

Swagger UI **v4 clássica** (assets servidos localmente, sem CDN), rota `/swagger`.
Detalhes por endpoint: exemplos de request/response, códigos de status, schemas,
tags por área (projects/chats/artifacts). Clique em **Authorize** e cole o
`DEVIAN_API_TOKEN` (sem o prefixo `Bearer `) para testar direto da página.
Seletor de servidores: **Produção** (via túnel) ou **Local** (porta 8088).
