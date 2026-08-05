# CLAUDE.md

Este arquivo orienta o desenvolvimento (humano ou IA) neste repositório. Para contexto geral do projeto, veja [README.md](README.md).

## Comandos

Todo comando Flutter/Dart é prefixado por `fvm` (o projeto fixa a versão do Flutter via `.fvmrc`):

```bash
fvm flutter pub get
fvm flutter analyze
fvm dart format lib test
fvm flutter test
fvm flutter test --coverage
```

Nunca rode `flutter`/`dart` sem o prefixo `fvm`.

## Padrões de Idioma

- **Comunicação**: sempre em português.
- **Código**: identificadores e comentários sempre em inglês.
- **Strings visíveis ao usuário** (mensagens de erro, textos de UI): sempre em português. Sem framework de i18n — o app é local.

## Dependências

Este projeto consome as dependências diretamente — `dio` (HTTP), `hive_ce` (cache local), `flutter_secure_storage` (dado sensível), `get_it` (DI), `go_router` (rotas), Material do Flutter (design system). Sem pacote próprio de abstração, sem generators/`build_runner`, sem `equatable`, sem `dartz` (`Either`/`Failure` são implementação própria do projeto). Veja [docs/dependencies_usage.md](docs/dependencies_usage.md).

## Arquitetura

Clean Architecture com módulos (`domain`/`infrastructure`/`external`/`presentation`). Antes de criar ou alterar qualquer módulo, leia [docs/architecture.md](docs/architecture.md).

## Referência rápida — se for fazer X, leia Y

| Se for...                                                                                | Leia                                                     |
| ---------------------------------------------------------------------------------------- | -------------------------------------------------------- |
| Criar ou alterar um módulo (camadas, boundaries, DI, rotas)                              | [docs/architecture.md](docs/architecture.md)             |
| Usar qualquer dependência direta (HTTP, cache, storage, DI, validators, design system)   | [docs/dependencies_usage.md](docs/dependencies_usage.md) |
| Nomear uma classe ou arquivo novo                                                        | [docs/naming_conventions.md](docs/naming_conventions.md) |
| Implementar repository, mapper, ou lidar com erro/exceção                                | [docs/error_handling.md](docs/error_handling.md)         |
| Escrever qualquer teste                                                                  | [docs/testing_guide.md](docs/testing_guide.md)           |
| Criar qualquer classe nova (qual modificador Dart 3 usar)                                | [docs/class_modifiers.md](docs/class_modifiers.md)       |
| Criar task ou implementar tela que precisa de fidelidade visual a uma referência (imagem/print ou descrição textual)        | [docs/design_workflow.md](docs/design_workflow.md)        |

## Fluxo de Trabalho

Este projeto usa um squad de agentes de IA para desenvolvimento assistido: **PO → Tech Lead → Dev Senior → QA**. Definição completa em [.claude/agents/](.claude/agents/) e [.claude/commands/](.claude/commands/).

Todo plano de feature (SDD) fica versionado em `./plans/<data>_<slug>.md`, onde `<data>` é a data de criação no formato `YYYY-MM-DD` e `<slug>` é um slug curto (2-4 palavras, kebab-case) gerado a partir da demanda — leia o SDD antes de implementar.

## Commits

Nunca rode `git commit` ou `git push` sem confirmação explícita do usuário, mesmo que ele peça em linguagem informal ("commita isso", "salva"). Sempre mostre a mensagem proposta e aguarde aprovação.
