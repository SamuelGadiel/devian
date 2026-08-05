# Modificadores de Classe (Dart 3)

Convenção adotada em **todas** as classes do projeto: nunca usar `class` simples quando um modificador mais específico se aplica. Modificador é escolhido pelo uso real da classe — o mais restritivo que ainda permite o que a classe precisa fazer (instanciar, estender, implementar).

## Modificadores disponíveis

- `class` — apenas quando nenhum outro se aplica
- `base class` — instanciável e extensível, não implementável
- `interface class` — instanciável e implementável, não extensível
- `final class` — só instanciável (não extensível, não implementável)
- `sealed class` — não instanciável, não extensível; permite implementação só dentro do mesmo arquivo (pattern matching exaustivo)
- `abstract class` / `abstract base class` / `abstract interface class` — variações não instanciáveis dos modificadores acima
- `abstract final class` — não instanciável, namespace estático (sem instância, sem herança)
- `mixin` / `mixin class` e variações `base` — quando a classe é usada como mixin

## Mapeamento por artefato

| Artefato                                        | Modificador                                    | Motivo                                                                      |
| ----------------------------------------------- | ---------------------------------------------- | --------------------------------------------------------------------------- |
| Entidade (`domain/entities/`)                   | `final class`                                  | Não precisa ser estendida nem implementada por outra classe                 |
| Abstração (repository, datasource, usecase)     | `abstract interface class`                     | Existe só pra ser implementada/mockada — nunca instanciada, nunca estendida |
| Implementação (repository, datasource, usecase) | `final class`                                  | Implementa a interface, não precisa ser estendida por mais ninguém          |
| Mapper                                          | `abstract final class`                         | Namespace estático — nunca instanciado, só métodos estáticos                |
| Failure (`domain/failures/`)                    | `final class` (`implements Failure`)           | Dado de erro, sem necessidade de herança adicional                          |
| Bloc                                            | `final class` (estende `Bloc<Events, States>`) | Implementação concreta, não precisa ser estendida                           |
| Evento/Estado (base sealed)                     | `sealed class`                                 | Enum-like — pattern matching exaustivo sobre os cases                       |
| Evento/Estado (case)                            | `final class` (implementa o sealed base)       | Cada case é uma implementação concreta e final                              |

## Igualdade (`==`/`hashCode`)

Sem `Equatable` no projeto. O único artefato que precisa de `==`/`hashCode` sobrescritos manualmente é o **Estado do Bloc** (case que carrega dado) — é o único ponto do projeto onde duas instâncias construídas separadamente (o estado emitido pelo Bloc e o estado esperado no `blocTest`) precisam ser comparadas por valor. Evento não precisa (nunca é comparado por `blocTest`, só disparado via `bloc.add`). Entidade e Failure também não — comparação de negócio é feita por propriedade específica (ex.: `user.id == other.id`), nunca por instância completa.

```dart
final class LoginSuccessState implements AuthStates {
  final User user;

  const LoginSuccessState(this.user);

  @override
  bool operator ==(Object other) => other is LoginSuccessState && other.user == user;

  @override
  int get hashCode => user.hashCode;
}
```

## Ordem dos membros

Propriedades usadas no construtor vêm **antes** do construtor; propriedades não recebidas por construtor podem vir depois.

```dart
final class LoginEvent implements AuthEvents {
  final String email;
  final String password;

  const LoginEvent({required this.email, required this.password});
}
```
