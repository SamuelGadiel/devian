# Devian Hub API

Backend do Devian — conecta o app Flutter ao Claude Code (container `devian`, Oracle).
Exposto via túnel Cloudflare `oracle-hermi`: `https://api.agapech.com.br/devian`.

## Stack
- **FastAPI** (Python 3.11) montado em `/devian` (cloudflared não stripa prefixo)
- **PostgreSQL 16** — container `devian-db` (127.0.0.1:5434, rede `devian-net`)
- **Claude Code** — `docker exec devian claude -p` (headless, workdir = pasta do projeto)
- **Storage local** — `/home/ubuntu/devian/storage/artefatos/<projeto_id>/`

## Endpoints (todos sob `/devian`, exceto `/health` exigem Bearer token)

### Projetos
| Método | Rota | Descrição |
|---|---|---|
| GET | `/projetos` | Lista projetos |
| POST | `/projetos` | Cria projeto (nome, repo_url, branch_padrao, caminho_container) |
| GET | `/projetos/{id}` | Detalhe |
| PUT | `/projetos/{id}` | Atualiza (nome, repo_url, branch, caminho) |
| DELETE | `/projetos/{id}` | Deleta (cascata: chats, msgs, artefatos) |

### Chats (1 chat = 1 sessão Claude)
| Método | Rota | Descrição |
|---|---|---|
| GET | `/chats?projeto_id=N` | Lista chats (recentes primeiro) |
| POST | `/chats` | Cria chat `{projeto_id, name?}` |
| GET | `/chats/{id}` | Detalhe |
| DELETE | `/chats/{id}` | Deleta chat + histórico |
| PUT | `/chats/{id}/rename` | Renomeia `{name}` |
| GET | `/chats/{id}/mensagens?cursor=&limit=` | Histórico paginado (cursor-based) |
| POST | `/chats/{id}/mensagens` | Envia msg `{conteudo}` — app manda SÓ a última msg |

### Artefatos (storage no servidor)
| Método | Rota | Descrição |
|---|---|---|
| GET | `/projetos/{id}/artefatos` | Lista artefatos |
| GET | `/projetos/{id}/artefatos/{id}` | Download |

## Regras de negócio
- **Payload leve**: o app envia só a última mensagem. Contexto = sessão Claude no container (--resume) + histórico no Postgres.
- **1 chat = 1 sessão**: primeira msg cria sessão (--session-id), demais retomam (--resume <id>).
- **Slug do chat**: name default "novo-chat" vira slug da 1ª mensagem (ex: "qual-a-cor").
- **Camada por projeto**: Claude roda com `-w /workspace/<projeto>` → carrega CLAUDE.md/.claude.

## Rodar
```bash
cd backend
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env   # DEVIAN_API_TOKEN, DATABASE_URL, STORAGE_DIR
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8088
```
Produção: systemd `devian-backend.service` (porta 8088; 8080 = SearXNG).
