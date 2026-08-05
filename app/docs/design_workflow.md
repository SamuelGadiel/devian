# Fluxo de Design

Este documento orienta como garantir fidelidade visual ao implementar uma tela ou fluxo — não decide **como** implementar (qual widget, componente ou padrão estrutural usar), só **com o que comparar** o resultado visual.

## Fonte da referência visual, nesta ordem de prioridade

1. **Imagem/print de referência** — passada pelo usuário para a tela/componente em implementação (mockup, protótipo, print de outra ferramenta, screenshot de um app similar).
2. **Descrição em texto** — passada pelo usuário, do que a tela deve conter, quando não houver imagem de referência.

Se nenhuma referência foi passada para a tarefa em questão, **pergunte ao usuário antes de assumir** — não existe fallback automático (não busque protótipos antigos ou arquivos de design não referenciados na conversa).

## O que este fluxo cobre — e o que não cobre

- **Cobre:** fidelidade visual — cores, espaçamento, tipografia, copy, estados dos componentes — ao que foi fornecido como referência.
- **Não cobre:** decisão estrutural de implementação (que widget do Flutter usar, se é um dropdown ou um bottom sheet, etc.). Isso segue os padrões já estabelecidos no projeto e no Material do Flutter — ver seção seguinte.

## Antes de implementar qualquer tela, componente ou widget — confira o que já existe

Nunca construa algo do zero sem antes verificar:

- **O que já existe implementado no projeto** (`lib/`) — telas, widgets e módulos semelhantes já construídos. Reaproveite o que já existe e mantenha consistência com o padrão já estabelecido, em vez de duplicar ou reinventar.
- **O que já existe disponível no Material do Flutter** (widgets, tema, capacidades nativas) — ver [docs/dependencies_usage.md](dependencies_usage.md). Implemente o mínimo necessário usando o que o próprio framework já oferece; nunca reescreva um widget que o Material já resolve.

## Quando não há imagem de referência (só descrição em texto)

Cruze as seguintes fontes para montar a tela:

- A descrição em texto fornecida pelo usuário.
- Os componentes, padrões visuais e temas já usados em outras telas do projeto e no Material do Flutter.

O objetivo é seguir a mesma lógica e o mesmo padrão visual já estabelecido no restante do app — não inventar um estilo novo.
