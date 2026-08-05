# CLAUDE.md

Orientação de desenvolvimento para este monorepo. Contexto geral do ecossistema em [README.md](README.md).

Este repositório tem dois contextos distintos, cada um com seu próprio padrão. Identifique em qual você está atuando antes de tocar em código.

## App Flutter (`app/`)

Se a tarefa envolve o app mobile, **leia e siga [app/CLAUDE.md](app/CLAUDE.md)** antes de qualquer alteração — ele define comandos (`fvm`), arquitetura (Clean Architecture por módulos), convenções de nomenclatura, tratamento de erro, testes e o squad de agentes (PO → Tech Lead → Dev Senior → QA) usado nesse projeto. Não aplique convenções deste arquivo raiz ao código do app; `app/CLAUDE.md` é a fonte de verdade ali.

## Backend (`backend/`) e workflows (`.github/workflows/`)

Se a tarefa envolve a Devian Hub API ou o CI, siga os padrões já estabelecidos em [backend/README.md](backend/README.md) (stack, endpoints, regras de negócio — IDs UUIDv7, erros em `{"message": "..."}`, datas em horário de Brasília, API em inglês/textos de usuário em português) e a convenção existente em `.github/workflows/build.yml`. Não há `CLAUDE.md` próprio nesse contexto — mantenha consistência com o código e a documentação já presentes em vez de introduzir um padrão novo.

## Commits

Nunca rode `git commit` ou `git push` sem confirmação explícita do usuário. Sempre mostre a mensagem proposta e aguarde aprovação.
