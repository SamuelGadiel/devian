# Comando: /techlead [slug (opcional)]

Realiza revisão técnica do SDD e cria plano de implementação.

**Uso:**

- `/techlead` → Pergunta qual SDD ou busca o mais recente em `./plans/`
- `/techlead login-redesign` → Busca o SDD mais recente com esse slug em `./plans/<data>_login-redesign.md`
- `@techlead_flutter` → Conversa natural (se PO não chamou automaticamente)

---

## Comportamento

1. **Spawn do agente Tech Lead:**
   - Invoca o agente `techlead_flutter` definido em `.claude/agents/techlead_flutter.md`

2. **Fluxo do agente:**
   - Lê `./plans/<data>_<slug>.md` (seções 1-9)
   - Lê `docs/architecture.md`, `docs/dependencies_usage.md`, `docs/naming_conventions.md`, `docs/error_handling.md`, `docs/testing_guide.md`, `docs/class_modifiers.md`
   - Identifica impacto por módulo/camada
   - Se identificar necessidade de alterar algum `docs/*.md`, **apresenta a proposta ao usuário antes de editar** (ver `.claude/agents/techlead_flutter.md`)
   - **Incrementa** `./plans/<data>_<slug>.md` adicionando **Seção 10** (técnico)
   - **Chama automaticamente Dev Senior** via `SendMessage`

3. **Output esperado:**
   - SDD incrementado com Seção 10 (Revisão Técnica)
   - Dev Senior invocado automaticamente

---

## Notas

- Agente Tech Lead conhece a arquitetura deste projeto (módulos, camadas, DI, rotas) — não redecide o que já está em `docs/*.md`.
- **Não cria arquivo novo**: incrementa o mesmo SDD criado pelo PO.
- Usuário não precisa chamar `/dev` manualmente — Tech Lead faz isso automaticamente.
