# SDD — [Nome da Feature]

**Slug:** [slug da feature]
**Status:** Draft | Em revisão | Aprovado
**Data:** YYYY-MM-DD
**Autor:** PO

---

## 1. Contexto

[Descreva o cenário atual e por que essa feature é necessária. 2-4 parágrafos.]

---

## 2. Objetivo

[Descreva o que essa feature entrega ao usuário e ao sistema. Bullet points são bem-vindos.]

---

## 3. Entidades Envolvidas

| Entidade     | Papel nesta feature  |
| ------------ | -------------------- |
| [Entidade 1] | [Descrição do papel] |

---

## 4. Requisitos Funcionais

| ID    | Requisito                                        |
| ----- | ------------------------------------------------ |
| RF-01 | O sistema deve permitir [ação] quando [condição] |

---

## 5. Regras de Negócio

| ID    | Regra                                        |
| ----- | -------------------------------------------- |
| RN-01 | [Entidade] não pode [ação] quando [condição] |

---

## 6. Requisitos Não-Funcionais

| ID     | Requisito                                                                   |
| ------ | --------------------------------------------------------------------------- |
| RNF-01 | **Performance:** [Ex.: tempo de resposta < 2s para 90% das requisições]     |
| RNF-02 | **Conectividade:** [Ex.: comportamento offline, sincronização]              |
| RNF-03 | **Acessibilidade:** [Ex.: suporte a leitores de tela]                       |
| RNF-04 | **Segurança:** [Ex.: dados sensíveis persistidos via `FlutterSecureStorage`] |

---

## 7. Casos de Uso

### UC-01 — [Nome do Caso de Uso]

**Ator:** [Usuário / Sistema]
**Pré-condição:** [Estado necessário antes de iniciar]

**Fluxo principal:**

1. Usuário [ação]
2. Sistema [resposta]

**Fluxo alternativo:**

- **FA-01:** Se [condição alternativa], então [comportamento]

**Pós-condição:** [Estado do sistema após conclusão]

---

## 8. Edge Cases

| Caso                       | Comportamento esperado                                                       |
| -------------------------- | ---------------------------------------------------------------------------- |
| Sem conexão durante [ação] | [Ex.: mensagem de erro, sem persistência local se não fizer parte do escopo] |
| Dados inválidos na entrada | Validação via `Validator` próprio do projeto (`shared/validators/`), mensagem em português |
| Timeout de API             | [Comportamento definido]                                                     |

---

## 9. Fora de Escopo

> Itens explicitamente **não** cobertos por esta feature:
>
> - [Item 1]

---

## 10. Revisão Técnica

> **Preenchida pelo Tech Lead após aprovação das seções 1-9.** Antes de incrementar esta seção com algo que também altere um doc em `docs/*.md` (novo padrão, nova convenção), o Tech Lead **apresenta a proposta ao usuário e aguarda aprovação** — nunca edita `docs/*.md` por conta própria.

**Autor:** Tech Lead
**Data:** YYYY-MM-DD

### 10.1 Impacto por Camada/Módulo

| Módulo     | Camada           | Arquivo(s) afetado(s)                                                                                | Ação            |
| ---------- | ---------------- | ---------------------------------------------------------------------------------------------------- | --------------- |
| `[module]` | `domain`         | `lib/modules/[module]/domain/entities/[entity].dart`                                                 | Criar/Modificar |
| `[module]` | `domain`         | `lib/modules/[module]/domain/repositories/[module]_repository.dart`                                  | Criar/Modificar |
| `[module]` | `domain`         | `lib/modules/[module]/domain/usecases/[verb].dart`                                                   | Criar/Modificar |
| `[module]` | `infrastructure` | `lib/modules/[module]/infrastructure/repositories/[module]_repository_implementation.dart`           | Criar/Modificar |
| `[module]` | `infrastructure` | `lib/modules/[module]/infrastructure/mappers/[entity]_mapper.dart`                                   | Criar/Modificar |
| `[module]` | `external`       | `lib/modules/[module]/external/datasources/{remote,local}/[module]_*_datasource_implementation.dart` | Criar/Modificar |
| `[module]` | `presentation`   | `lib/modules/[module]/presentation/blocs/[nome]_bloc/*`                                              | Criar/Modificar |
| `[module]` | `presentation`   | `lib/modules/[module]/presentation/pages/[nome]_page.dart`                                           | Criar/Modificar |
| —          | DI               | `lib/core/service_locator/binds/[module]_binds.dart`                                                 | Criar/Modificar |
| —          | Rotas            | `lib/core/router/routes/[module]_routes.dart`                                                        | Criar/Modificar |

_(Módulo pode não precisar de todas as camadas — ver [docs/architecture.md](../../docs/architecture.md#módulo-cresce-incrementalmente).)_

### 10.2 Decisões de Arquitetura

| Decisão                            | Alternativa considerada | Justificativa   |
| ---------------------------------- | ----------------------- | --------------- |
| [Decisão específica desta feature] | [Alternativa]           | [Justificativa] |

_(Decisões já cobertas por `docs/_.md` não precisam ser repetidas aqui — só o que é específico desta feature.)\*

### 10.3 Tarefas Técnicas

| ID     | Módulo/Camada     | Descrição   | Complexidade |
| ------ | ----------------- | ----------- | ------------ |
| TSK-01 | `[module]`/domain | [Descrição] | P/M/G        |

**Complexidade:** P (pequena) / M (média) / G (grande)

### 10.4 Riscos Técnicos

| Risco   | Impacto          | Mitigação   |
| ------- | ---------------- | ----------- |
| [Risco] | Alto/Médio/Baixo | [Mitigação] |

### 10.5 Observações

- [Notas adicionais sobre implementação, aprendizado específico desta feature que não vira regra de projeto]
