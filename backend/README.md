# Devian Hub API

Backend do Devian — conecta o app Flutter ao Claude Code (container `devian`, Oracle).
Exposto via túnel Cloudflare `oracle-hermi`: `https://api.agapech.com.br/devian`.

## Stack
- **FastAPI** (Python 3.11) montado em `/devian` (cloudflared não stripa prefixo)
- **PostgreSQL 16** — container `devian-db` (127.0.0.1:5434, rede `devian-net`)
- **Claude Code** — `docker exec devian claude -p` (headless, workdir = pasta do projeto)
- **Storage local** — `/home/ubuntu/devian/storage/artifacts/<project_id>/`
- **IDs**: UUIDv7 em tudo (ordenável por tempo → paginação por cursor funciona)

## Endpoints (todos sob `/devian`, exceto `/health` exigem Bearer token)

### Projects
| Método | Rota | Descrição |
|---|---|---|
| GET | `/projects` | Lista projetos |
| POST | `/projects` | Cria projeto `{name, repo_url?, branch?}` |
| GET | `/projects/{project_id}` | Detalhe |
| PUT | `/projects/{project_id}` | Atualiza (name, repo_url, branch) |
| DELETE | `/projects/{project_id}` | Deleta (cascata: chats, messages, artifacts) |

### Chats (1 chat = 1 sessão Claude; escopo do projeto)
| Método | Rota | Descrição |
|---|---|---|
| GET | `/projects/{project_id}/chats` | Lista chats (recentes primeiro) |
| POST | `/projects/{project_id}/chats` | Cria chat `{name?}` — herda branch do projeto |
| GET | `/projects/{project_id}/chats/{chat_id}` | Detalhe |
| DELETE | `/projects/{project_id}/chats/{chat_id}` | Deleta chat + histórico |
| PUT | `/projects/{project_id}/chats/{chat_id}/rename` | Renomeia `{name}` |

### Messages (escopo do chat)
| Método | Rota | Descrição |
|---|---|---|
| GET | `/projects/{project_id}/chats/{chat_id}/messages?cursor=&limit=` | Histórico paginado (cursor = UUID) |
| POST | `/projects/{project_id}/chats/{chat_id}/messages` | Envia msg `{content}` — app manda SÓ a última msg |

### Artifacts (storage no servidor; escopo do projeto)
| Método | Rota | Descrição |
|---|---|---|
| GET | `/projects/{project_id}/artifacts` | Lista artifacts |
| GET | `/projects/{project_id}/artifacts/{artifact_id}` | Download |

## Regras de negócio
- **Payload leve**: o app envia só a última mensagem. Contexto = sessão Claude no container (--resume) + histórico no Postgres.
- **1 chat = 1 sessão**: primeira msg cria sessão (--session-id), demais retomam (--resume <id>).
- **Slug do chat**: name default "new-chat" vira slug da 1ª mensagem (ex: "qual-a-cor").
- **Branch**: o projeto tem a branch de trabalho (`branch`, ex: develop); chats herdam a branch do projeto.
- **Camada por projeto (interno)**: `container_path` é derivado do repo_url (ex: `/workspace/sisvisa-serr-mobile`), validado no container em runtime e **não é exposto na API**.
- **API em inglês**: endpoints, parâmetros, payloads e responses em inglês; só textos exibidos ao usuário final ficam em português.
- **IDs UUIDv7**: todos os ids (project, chat, message, artifact) são UUID v7 — ordenáveis por tempo; `next_cursor` é o UUID da msg mais antiga da página.
- **Fuso horário**: banco armazena UTC (timestamptz); API retorna **todas** as datas em **ISO 8601 / RFC 3339 em Brasília** — `2026-08-05T17:44:40-03:00` (sem fração). O app faz `DateTime.parse(...)` direto (Dart devolve `isUtc=false` com a hora local do aparelho — sem `.toLocal()`). A infra (host, Postgres, container) opera em America/Sao_Paulo.
- **Erros**: **todos** os erros respondem `{"message": "..."}` (nunca `detail`). Validação 422 inclui `errors: [{field, message}]`.

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
Seções em TitleCase (Projects, Chats, Messages, Artifacts, Health), descrição curta
em cada endpoint. Clique em **Authorize** e cole o `DEVIAN_API_TOKEN` (sem o prefixo
`Bearer `) para testar direto da página. Seletor de servidores: **Produção** (via
túnel) ou **Local** (porta 8088).
