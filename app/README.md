# Devian (App Flutter)

Cliente mobile do ecossistema **Devian** — a interface que tira o fluxo de desenvolvimento do MacBook e leva para o servidor, com o celular como porta de entrada. Contexto completo do ecossistema no [README raiz](../README.md).

Hoje, desenvolver o **SISVISA SERR Mobile** exige a máquina local: conversar com a IA de desenvolvimento, rodar o Claude Code, buildar o APK. Este app move esse ciclo inteiro para o celular — conversa com o agente de código, acompanha o progresso e baixa o APK gerado, tudo pelo chat.

## O que o app faz

- **Projetos** — lista os projetos existentes (ex.: SISVISA SERR Mobile), cada um ligado a um repositório.
- **Chats** — cada projeto tem um ou mais chats; cada chat é uma sessão contínua com o agente de código (Claude Code), que mantém o contexto da conversa anterior.
- **Mensagens** — o usuário manda tarefas em linguagem natural ("adiciona um botão de exportar PDF") e o agente responde.
- **Artefatos** — arquivos gerados pelo CI (ex.: APK) aparecem no chat e podem ser baixados e instalados direto no celular.

## Como se conecta ao resto do ecossistema

```
app (este projeto)
        │  HTTP + Bearer token
        ▼
Devian Hub API  (https://api.agapech.com.br/devian)
        │
        ├──► Claude Code (container Linux, repositório do projeto clonado)
        └──► CI do GitHub (builda o APK sob demanda)
```

O app não fala diretamente com o Claude Code nem com o CI — toda comunicação passa pela **Devian Hub API**, que orquestra ambos. Do ponto de vista do app, o backend expõe apenas recursos REST (`projects`, `chats`, `messages`, `artifacts`).

- **Base da API**: `https://api.agapech.com.br/devian`
- **Autenticação**: token Bearer
- **Contrato**: ver [backend/README.md](../backend/README.md) (na raiz do monorepo) e Swagger em `/devian/swagger`

## Stack e convenções

Flutter (SDK `^3.11.0`), Clean Architecture por módulos, `dio` + `hive_ce` + `flutter_secure_storage` + `get_it` + `go_router`. Ver [CLAUDE.md](CLAUDE.md) para comandos (`fvm`), padrões de idioma e squad de agentes, e [docs/](docs/) para arquitetura, convenções de nomenclatura, tratamento de erro e testes.

## Status

Projeto recém-criado (scaffold padrão `flutter create`) — nenhum módulo implementado ainda. A documentação em [docs/](docs/) e o [CLAUDE.md](CLAUDE.md) já definem o padrão a seguir antes da primeira feature.
