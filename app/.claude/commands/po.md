# Comando: /po [descrição livre]

Inicia o processo de refinamento de requisitos e criação do SDD (Software Design Document).

**Uso:**

- `/po` → Inicia refinamento (descrição pedida durante a conversa)
- `@po vamos implementar login` → Conversa natural (recomendado)

---

## Comportamento

1. **Spawn do agente PO:**
   - Invoca o agente `po` definido em `.claude/agents/po.md`

2. **Fluxo do agente:**
   - Se imagem/print de referência visual fornecida: usa como base para as especificações visuais
   - Refina requisitos com usuário (perguntas estratégicas)
   - Cria `./plans/<data>_<slug>.md` (seções 1-9: negócio), seguindo `.claude/templates/sdd_template.md`
   - **Chama automaticamente Tech Lead** via `SendMessage`

3. **Output esperado:**
   - SDD salvo em `./plans/<data>_<slug>.md`
   - Tech Lead invocado automaticamente

---

## Notas

- Agente PO é **genérico**: funciona para qualquer domínio de negócio deste projeto.
- SDD é salvo **no projeto atual**, versionado.
- Usuário não precisa chamar `/techlead` manualmente — PO faz isso automaticamente.
