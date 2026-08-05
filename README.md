# Devian

Ecossistema que tira o fluxo de desenvolvimento do MacBook e leva para o servidor, com o celular como interface.

Hoje, desenvolver o **SISVISA SERR Mobile** (Flutter) exige a máquina local: conversar com a IA de desenvolvimento, rodar o Claude Code, buildar o APK. O Devian move esse ciclo inteiro para um servidor na nuvem — o app no celular vira a porta de entrada, e o trabalho pesado roda lá.

## Visão geral do fluxo

```
celular (app Flutter)
        │  conversa com o assistente de cada projeto
        ▼
Devian Hub API  (FastAPI + Postgres, no servidor Oracle)
        │
        ├──► Claude Code (container Linux, repositório do projeto clonado)
        │         │  executa a tarefa de código
        │         ▼
        │   mudanças no código + resposta pro chat
        │
        └──► CI do GitHub (GitHub Actions)
                  │  builda o APK Android sob demanda
                  ▼
        APK volta pro chat como artefato → usuário baixa e instala
```

1. O usuário abre o app Flutter no celular e conversa com o assistente de um projeto.
2. A mensagem chega na **Devian Hub API**, que roda no servidor Oracle e é exposta em `https://api.agapech.com.br/devian`.
3. A API repassa a tarefa para o **Claude Code**, que roda em um container Linux no mesmo servidor, com o repositório do projeto disponível.
4. Cada chat é uma conversa contínua com o agente de código — o agente lembra o contexto da conversa anterior.
5. Quando a tarefa exige build, o **CI do GitHub** compila o APK Android.
6. O APK volta para o chat como artefato; o usuário baixa e instala direto no celular.

## Componentes

| Componente | O que é |
|---|---|
| **App Flutter** | Cliente mobile — chat com o assistente de IA de cada projeto. *(Em construção — é aqui que este trabalho entra.)* |
| **Devian Hub API** | Backend em `backend/` (FastAPI + Postgres). Gerencia projetos, chats, mensagens e artefatos, e orquestra o agente de código. |
| **Agente de código** | Claude Code rodando em container. Executa as tarefas diretamente no repositório do projeto, uma sessão por chat. |
| **CI** | GitHub Actions que builda o APK Android do app sob demanda. |

## Onde o app Flutter se encaixa

O app é a interface do ecossistema. Ele conversa com a Devian Hub API:

- **Projetos** — lista os projetos existentes (ex.: SISVISA SERR Mobile), cada um ligado a um repositório.
- **Chats** — cada projeto tem um ou mais chats; cada chat é uma conversa contínua com o agente de código.
- **Mensagens** — o usuário manda tarefas ("adiciona um botão de exportar PDF") e o agente responde.
- **Artefatos** — arquivos gerados (ex.: APK) aparecem no chat e podem ser baixados.

## API

- **Base**: `https://api.agapech.com.br/devian`
- **Documentação interativa**: `/devian/swagger` (Swagger UI) · schema em `/devian/openapi.json`
- **Autenticação**: token Bearer
- **Recursos**:
  - `GET /health` — status da API (público)
  - `GET/POST /projects`, `GET/PUT/DELETE /projects/{project_id}`
  - `GET/POST /projects/{project_id}/chats`
  - `GET/PUT/DELETE /projects/{project_id}/chats/{chat_id}`
  - `GET/POST /projects/{project_id}/chats/{chat_id}/messages`
  - `GET /projects/{project_id}/artifacts`, `GET .../artifacts/{artifact_id}` (download)

> Detalhes de contrato (formatos de data, erros, paginação) estão documentados no Swagger e no `backend/README.md`.

## Estrutura do repositório

```
backend/                    # Devian Hub API (FastAPI)
  app/                      #   aplicação (routers, schemas, models)
  docs/openapi.json         #   snapshot do schema OpenAPI
  static/swagger/           #   assets do Swagger UI
.github/workflows/build.yml # CI que builda o APK Android
storage/                    # artefatos gerados (local no servidor)
```
