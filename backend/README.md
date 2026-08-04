# Devian Hub API

Backend do Devian — o cérebro que conecta o app Flutter ao Claude Code
rodando no container `devian` (Oracle).

## Stack

- **FastAPI** (Python 3.11) — API HTTP, montada em `/devian`
- **PostgreSQL 16** — container `devian-db` (porta local 5434, rede `devian-net`)
- **Claude Code** — executado via `docker exec devian claude` (headless)

## Endpoints

| Método | Rota (prefixo `/devian`) | Descrição |
|---|---|---|
| GET | `/health` | Healthcheck (público) |
| POST | `/chat` | Envia mensagem; cria/retoma sessão Claude (1 chat = 1 sessão) |
| GET | `/chat/sessoes` | Lista sessões |
| GET | `/chat/sessoes/{id}` | Detalhe + mensagens da sessão |
| GET | `/projetos` | Lista projetos |
| POST | `/projetos` | Cria projeto |

Todas as rotas (exceto `/health`) exigem `Authorization: Bearer <DEVIAN_API_TOKEN>`.

## Modelo de dados

```
projetos (nome, repo_url, branch_padrao)
  └── sessoes (chat_id_app ↔ session_id_claude, branch, status)
       └── mensagens (role: user|assistant, conteudo)
            └── builds (run_id, status, artifact_url)   [em construção]
```

## Rodar

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env   # preencher DEVIAN_API_TOKEN e DATABASE_URL
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8088
```

Serviço systemd (produção): `devian-backend.service` — porta **8088**
(8080 é do SearXNG). Exposto ao mundo via túnel Cloudflare `oracle-hermi`
(`https://api.agapech.com.br/devian`).

## Segurança

- Token Bearer simples por enquanto (camada mínima).
- Será substituído por **Cloudflare Access (Zero Trust)** na fase do app.
- **Nunca** commitar `.env` (repo público).
