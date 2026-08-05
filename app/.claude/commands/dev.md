# Comando: /dev [slug (opcional)]

Implementa a feature conforme SDD e plano técnico.

**Uso:**

- `/dev` → Pergunta qual SDD ou busca o mais recente em `./plans/`
- `/dev login-redesign` → Busca o SDD mais recente com esse slug em `./plans/<data>_login-redesign.md`
- `@dev_senior_flutter` → Conversa natural (se Tech Lead não chamou automaticamente)

---

## Comportamento

1. **Spawn do agente Dev Senior:**
   - Invoca o agente `dev_senior_flutter` definido em `.claude/agents/dev_senior_flutter.md`

2. **Fluxo do agente:**
   - Lê `./plans/<data>_<slug>.md` (COMPLETO: seções 1-10)
   - Lê `docs/*.md`
   - Implementa camada por camada: `domain` → `infrastructure` → `external` → `presentation` → `core/service_locator/binds/` → `core/router/routes/`
   - Escreve testes junto com cada camada (mocktail + bloc_test)
   - Roda `fvm flutter test` após cada camada
   - Garante 100% de testes passando
   - Roda `fvm dart format lib test` no projeto inteiro
   - **Chama automaticamente QA** via `SendMessage`

3. **Output esperado:**
   - Código implementado em `lib/modules/<module>/`
   - Testes implementados em `test/modules/<module>/`
   - QA invocado automaticamente

---

## Notas

- Agente Dev Senior segue estritamente a Seção 10 do SDD (plano técnico do Tech Lead) e os padrões em `docs/*.md`.
- **Nunca commita, nem propõe commit** — isso é sempre feito pelo usuário, via `/commit`.
- Usuário não precisa chamar `/qa` manualmente — Dev Senior faz isso automaticamente após garantir testes passando.
