# Comando: /qa [slug (opcional)]

Valida a implementação contra SDD e padrões do projeto.

**Uso:**

- `/qa` → Pergunta qual SDD ou busca o mais recente em `./plans/`
- `/qa login-redesign` → Busca o SDD mais recente com esse slug em `./plans/<data>_login-redesign.md`
- `@qa_flutter` → Conversa natural (se Dev Senior não chamou automaticamente)

---

## Comportamento

1. **Spawn do agente QA:**
   - Invoca o agente `qa_flutter` definido em `.claude/agents/qa_flutter.md`

2. **Fluxo do agente:**
   - Lê `./plans/<data>_<slug>.md` (completo: seções 1-10)
   - Lê código implementado (arquivos listados na Seção 10.1)
   - Valida: RF-XX, RN-XX, RNF-XX, Edge Cases, arquitetura (camadas, boundaries entre módulos, anti-patterns), cobertura de testes
   - Roda `fvm flutter test` independentemente
   - Roda `fvm dart format --output=none --set-exit-if-changed lib test` (dry-run) para validar formatação
   - Gera **Relatório de Validação** em tabela

   **Se aprovado (✅):** informa que pode ser integrado a `develop`.
   **Se reprovado (❌):** lista itens a corrigir com prioridade e **chama Dev Senior** via `SendMessage`.

3. **Output esperado:**
   - Relatório de validação completo em tabela
   - Decisão final clara (✅ Aprovado / ⚠️ Ressalvas / ❌ Reprovado)
   - Se reprovado: Dev Senior invocado automaticamente com lista de correções

---

## Notas

- Agente QA valida contra `docs/*.md` deste projeto (não uma arquitetura genérica).
- Tem **autoridade para reprovar**: feature não sobe sem aprovação do QA.
- Roda `fvm flutter test` **independentemente** (validação dupla).
- Roda `fvm dart format --output=none --set-exit-if-changed lib test` **independentemente**, em modo dry-run (nunca altera arquivos) — reprova se o projeto não estiver formatado.
- Se reprovado, Dev Senior é chamado automaticamente para correções.
