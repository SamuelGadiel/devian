# Comando: /commit [scope]

Cria commits atômicos seguindo **Conventional Commits 1.0.0** a partir das mudanças pendentes no repositório.

**Uso:**

- `/commit` → commits sem scope: `feat: add feature`
- `/commit login-redesign` → commits com scope: `feat(login-redesign): add feature`

---

## FLUXO OBRIGATÓRIO (SIGA NA ORDEM, SEM PULAR ETAPAS)

### FASE 1: ANÁLISE (não exiba nada ao usuário ainda)

**1.1 Captura de parâmetros:**

- Se houver argumento após `/commit`, capture como scope (sem validação de formato — tipicamente o slug do SDD em `./plans/`, se houver um relacionado)
- Exemplo: `/commit login-redesign` → scope = `login-redesign`
- Se não houver argumento → scope = vazio (sem parênteses na mensagem)

**1.2 Análise de mudanças:**

Execute em paralelo:

- `git status` (sem flag `-uall`)
- `git diff` (staged + unstaged)

Identifique:

- Arquivos modificados/criados/deletados
- Contexto de cada mudança (feature, fix, refactor, etc)
- Agrupamento lógico por propósito
- **Type apropriado** para cada grupo (baseado no diff + contexto):
  - `feat` — nova funcionalidade, novos arquivos de feature
  - `fix` — correção de bugs, validações, tratamento de erro
  - `refactor` — mudança de estrutura sem alterar comportamento
  - `perf` — otimizações de performance
  - `test` — apenas testes
  - `docs` — apenas documentação
  - `style` — formatação, lint (sem lógica)
  - `build` — dependências, configs de build
  - `ci` — CI/CD, pipelines
  - `chore` — manutenção, configs gerais

**Regra crítica de atomicidade:**

- Cada commit deve ter **um único propósito claro**
- Agrupe arquivos relacionados ao mesmo contexto
- Se um arquivo tem mudanças de 2 contextos diferentes: coloque no commit **mais relevante** (não quebrar arquivo entre commits)
- Arquivos de teste/exemplo vão junto com os arquivos core relacionados

**Granularidade por camada (Clean Architecture: `domain`/`infrastructure`/`external`/`presentation` + DI):**

Quando as mudanças de um mesmo propósito cruzam múltiplas camadas, decida o nível de quebra pela **natureza** da mudança, não pela quantidade de arquivos:

- **Estrutura nova, construída do zero** (nova entidade/fluxo, ou módulo inteiro novo) → quebre **um commit por camada**, cada um com seus testes correspondentes, sempre nesta ordem: `domain` → `infrastructure` → `external` → `presentation` → DI/wiring (`binds`, `locator`, `routes`) como commit `chore` separado ao final.
  - Exemplo: criar módulo `contacts` do zero = 1 commit `feat` de domain, 1 de infra, 1 de external, 1 de presentation, 1 `chore` de wiring — nunca tudo junto.
- **Rename/movimentação mecânica** (troca de nome de identificador/arquivo/import, sem mudar comportamento, ainda que toque várias camadas) → **um único commit** `refactor`, mesmo cruzando camadas. Quebrar por camada não agrega clareza a um rename.
- **Integração/modificação pontual em código já existente** (ex.: módulo passa a consumir algo de outro módulo, troca a origem de um dado, ajusta uma dependência) → **um único commit** cobrindo a mudança de ponta a ponta, mesmo cruzando `domain`/`presentation`/DI, salvo se o volume de arquivos justificar dividir.
- Arquivo de DI/wiring que mistura referências de rename **e** de estrutura nova no mesmo diff (ex.: um `binds.dart` que registra o item renomeado e os itens novos juntos) → entra no commit mais relevante (o de estrutura nova), nunca é quebrado entre commits.
- Na dúvida entre agrupar ou quebrar, prefira **menos commits para mudanças simples/específicas** e **mais commits (por camada) para construção nova**.

**Exclusões automáticas:**

- Ignore apenas `PLAN.md`/`TODO.md` soltos na **raiz do repositório** (rascunho pessoal não versionado), a menos que usuário solicite explicitamente
- **Inclua normalmente** `CLAUDE.md`, docs de projeto, e SDDs em `./plans/*.md` — são versionados por padrão neste projeto

---

### FASE 2: PROPOSTA (exiba para o usuário e PARE)

Exiba a proposta no seguinte formato:

```
## Proposta de Commits

**Commit 1**
`<mensagem do commit>`

Arquivos:
- `<caminho/arquivo1>`
- `<caminho/arquivo2>`

---

**Commit 2**
`<mensagem do commit>`

Arquivos:
- `<caminho/arquivo3>`

---

Total: X commit(s)
```

**Regras de mensagem (Conventional Commits 1.0.0):**

**Formato obrigatório:**

- **Com scope**: `<type>(<scope>): <description>`
- **Sem scope**: `<type>: <description>`

Exemplo:

- `feat(login-redesign): add user authentication module`
- `fix: resolve validation error on login`

**Regras da description:**

- Inglês, lowercase, imperativo
- Sem pontuação final
- Completa a frase "this commit will..." (ex: "add login flow", "fix validation bug")
- Mensagem **completa** ≤72 caracteres (incluindo type + scope)

**Se exceder 72 caracteres:**

- Abrevia palavras comuns (`authentication` → `auth`, `configuration` → `config`)
- Remove artigos desnecessários (`the`, `a`, `an`)
- Simplifica verbos (`implement` → `add`, `modify` → `update`)
- Mantém clareza: prefere mensagem levemente genérica a truncar

**Types válidos:**

- `feat`, `fix`, `refactor`, `perf`, `test`, `docs`, `style`, `build`, `ci`, `chore`

**NUNCA use:**

- Body (segunda linha em diante)
- Footer (Refs, BREAKING CHANGE, etc)
- Apenas a primeira linha no formato especificado

**APÓS EXIBIR A PROPOSTA:**

- **PARE IMEDIATAMENTE**
- **NÃO execute git add**
- **NÃO execute git commit**
- **AGUARDE aprovação explícita do usuário**

Se o usuário pedir ajustes, refaça a proposta e aguarde novamente.

---

### FASE 3: EXECUÇÃO (somente após aprovação explícita)

Para cada commit aprovado, execute **sequencialmente** (um de cada vez):

1. `git add <arquivo1> <arquivo2> ...` (liste todos os arquivos do commit)
2. `git commit -m "<mensagem>"`
3. Aguarde o commit finalizar antes de ir para o próximo

**Regras de execução:**

- Use apenas `git add` (NUNCA use `git rm`)
- Execute commits um por vez (não paralelizar)
- Não use `--amend`, `--no-verify`, ou outras flags especiais
- Se um commit falhar, **PARE** e reporte o erro ao usuário

---

### FASE 4: FINALIZAÇÃO

Após todos os commits executados com sucesso, exiba apenas:

```
Feito.
```

Nada mais. Sem resumo, sem explicação adicional.

---

## DIAGRAMA DE FLUXO (para referência)

```
Análise (git status + diff)
         ↓
Agrupa mudanças por contexto
         ↓
Cria proposta estruturada
         ↓
EXIBE proposta ao usuário
         ↓
**PARA E AGUARDA APROVAÇÃO**
         ↓
Usuário aprova?
  ├─ Não → Aguarda ajustes
  └─ Sim → Executa commits (um a um)
         ↓
Exibe "Feito."
```

---

## EXEMPLO DE PROPOSTA VÁLIDA

**Com scope** (`/commit login-redesign`):

```
## Proposta de Commits

**Commit 1**
`feat(login-redesign): add user authentication module`

Arquivos:
- `lib/auth/auth_service.dart`
- `lib/auth/auth_repository.dart`
- `test/auth/auth_service_test.dart`

---

**Commit 2**
`refactor(login-redesign): simplify login page structure`

Arquivos:
- `lib/pages/login_page.dart`
- `lib/widgets/login_form.dart`

---

Total: 2 commit(s)
```

**Sem scope** (`/commit`):

```
## Proposta de Commits

**Commit 1**
`feat: add user authentication module`

Arquivos:
- `lib/auth/auth_service.dart`
- `lib/auth/auth_repository.dart`
- `test/auth/auth_service_test.dart`

---

**Commit 2**
`refactor: simplify login page structure`

Arquivos:
- `lib/pages/login_page.dart`
- `lib/widgets/login_form.dart`

---

Total: 2 commit(s)
```

---

## CHECKLIST INTERNO (não exiba ao usuário)

Antes de exibir proposta, verifique:

- [ ] Scope capturado corretamente do argumento (ou vazio se não informado)?
- [ ] Commits são atômicos (um propósito cada)?
- [ ] Type apropriado inferido para cada commit?
- [ ] Mensagem completa ≤72 caracteres (incluindo `type(scope): `)?
- [ ] Formato Conventional Commits correto: `type(scope): description` ou `type: description`?
- [ ] Description em lowercase, imperativo, sem ponto final?
- [ ] Description completa "this commit will..."?
- [ ] Nenhum arquivo foi quebrado entre commits?
- [ ] Estrutura nova (do zero) foi quebrada por camada (domain/infra/external/presentation/DI)? Rename e integração pontual ficaram num commit só?
- [ ] Apenas `PLAN.md`/`TODO.md` na raiz (se existirem) foram excluídos — SDDs em `./plans/` foram incluídos normalmente?
- [ ] Proposta está formatada corretamente?
- [ ] **NUNCA** há body ou footer nas mensagens?

Somente após confirmar tudo: exiba proposta e **PARE**.
