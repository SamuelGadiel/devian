# Error Handling

## Fluxo: `Exception` → `Failure`

```
external (datasource)  →  lança Exception (nunca retorna Either)
        ↓
infrastructure (repository)  →  captura a Exception, converte pra Failure, retorna Either<Failure, T>
        ↓
domain (usecase)  →  repassa o Either (ou gera sua própria Failure de validação, sem exceção)
        ↓
presentation (Bloc)  →  fold(failure, success) → emite estado
```

- `external/` só lança `Exception` (idealmente `RequestException`/`CacheException` do próprio projeto — `core/errors/exceptions.dart` — quando fizer sentido) — nunca captura erro nem retorna `Either`.
- `infrastructure/repositories/` é a única camada que faz `try/catch`: captura a exceção do datasource e converte em `Failure` (`domain/failures/`), retornando sempre `Either<Failure, T>`.
- `domain/usecases/` nunca lança nem captura exceção — só repassa o `Either` do repository, ou constrói uma `Failure` de validação diretamente (sem passar por exceção nenhuma) quando a regra de negócio falha antes de chegar ao repository.
- `presentation/blocs/` nunca lida com `Exception` — só consome o `Either` já resolvido via `fold`.

## Onde a mensagem de erro mora

Não existe arquivo central de mensagens de erro. A mensagem vive no ponto de origem:

- **Falha de validação de negócio** (ex.: e-mail inválido, senha vazia) → mensagem definida no `domain`, no momento em que a `Failure` é construída.
- **Exceção técnica** (ex.: erro de rede, erro de cache) → mensagem definida onde a exceção é lançada, em `external/`/`infrastructure/`.

Toda mensagem visível ao usuário é em português (ver [CLAUDE.md](../CLAUDE.md)).

## Mapper: Entity ↔ JSON

Não existe Model/DTO no projeto — só `Mapper` (`infrastructure/mappers/`), com métodos estáticos de conversão. `external/` nunca referencia `Mapper` nem `Entity` — só `Map<String, dynamic>`/primitivos. O `infrastructure/repositories/` é sempre quem chama o `Mapper`, nas duas direções (detalhado em [architecture.md](architecture.md#direção-do-dado-quem-monta-o-json)).

Mapper só converte — nenhuma lógica de validação/negócio. Essa lógica mora na `Entity` (`domain/entities/`).
