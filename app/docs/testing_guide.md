# Guia de Testes

## Stack

- `flutter_test` — base.
- `mocktail` — mocks (repository, datasource, usecase). Nunca `mockito`.
- `bloc_test` — testes de Bloc (`blocTest`), asserindo sequência de estados emitidos.

## O que testar, por camada

| Camada                            | O que testar                                                                                                                                                                                                                         |
| --------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `domain/usecases/`                | Caminho feliz + repassar `Failure` do repository (mockado via `mocktail`) + `Failure` de validação gerada pelo próprio usecase, sem repository envolvido (ex.: e-mail vazio retorna `Left` antes de qualquer chamada ao repository). |
| `infrastructure/repositories/`    | Conversão `Exception → Failure` e `JSON ↔ Entity` (via Mapper). Datasource é mockado via `mocktail`, cobrindo sucesso e exceção.                                                                                                     |
| `external/datasources/`           | Chamada ao `Client`/`CacheService`, retorno de dado bruto ou exceção lançada.                                                                                                                                                        |
| `presentation/blocs/`             | Sequência de estados emitida por evento, via `blocTest`. Usecase é mockado via `mocktail`. Cobre caminho feliz + falha.                                                                                                              |
| `presentation/pages/`, `widgets/` | Nível de interação/estado — `pump`, `tap`, `verify`. Sem golden test — os componentes são widgets Material nativos do Flutter, já testados pelo próprio framework.                                                                                                         |

Todo teste cobre **caminho feliz + caminho de erro** — não só o caso de sucesso.

## Estrutura

Um arquivo de teste por arquivo de produção, espelhando `lib/` em `test/`:

```
lib/modules/auth/domain/usecases/login.dart
test/modules/auth/domain/usecases/login_test.dart
```

Nome do teste = nome do arquivo de produção + `_test.dart` (ver [naming_conventions.md](naming_conventions.md)).

## Exemplo — `blocTest`

```dart
blocTest<AuthBloc, AuthStates>(
  'emite LoginLoadingState e LoginSuccessState quando login é bem-sucedido',
  build: () {
    when(() => login(any())).thenAnswer((_) async => Right(user));
    return AuthBloc(login);
  },
  act: (bloc) => bloc.add(LoginEvent(email: email, password: password)),
  expect: () => [LoginLoadingState(), LoginSuccessState(user)],
);
```

## Cobertura

Meta de 80%, **não bloqueante**. Verificação acontece via script em `automation/scripts` que roda os testes com cobertura e imprime a porcentagem — não há gate automático em pipeline; divergência de cobertura é resolvida no ciclo QA↔Dev Senior antes da entrega.

## Rodando localmente

```bash
fvm flutter test
fvm flutter test --coverage
```

Todo comando é sempre prefixado por `fvm` (ver [CLAUDE.md](../CLAUDE.md)).
