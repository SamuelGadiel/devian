# Uso das Dependências

O projeto **não** usa um pacote próprio de abstração (tipo `mobile_core`). Cada necessidade é resolvida com uma dependência direta do `pubspec.yaml`, ou com um utilitário pequeno do próprio projeto quando não existe (ou não vale a pena) um pacote pronto. Nunca reescreva na mão algo que a dependência direta já resolve.

**Proibido neste projeto:** generators/`build_runner` (nenhum `.g.dart`), `equatable`, `dartz`. Ver seções abaixo para o que substitui cada um.

## HTTP (`dio`)

`external/datasources/remote/` usa `Dio` diretamente. A instância é configurada uma única vez em `core/network/dio_client.dart` (`baseUrl`, `validateStatus: (status) => true`, interceptors) e injetada via DI — datasource nunca instancia `Dio` na mão.

```dart
final response = await dio.post(ApiRoutes.login, data: {'email': email, 'password': password});

if (response.statusCode == null || response.statusCode! >= 400) {
  throw RequestException(message: 'Credenciais inválidas', statusCode: response.statusCode);
}

return response.data as Map<String, dynamic>;
```

> Endpoint sempre vem de `ApiRoutes` (`core/network/api_routes.dart`), nunca string literal — ver [architecture.md](architecture.md#external).

> **`validateStatus` sempre `true`.** Nenhum status HTTP (401, 400, 500...) lança `DioException` nesta stack — só falha real de conexão (timeout, sem rede) lança. Todo datasource remoto checa `response.statusCode` manualmente e lança `RequestException` quando for erro (ver [architecture.md](architecture.md#interceptors-corenetworkinterceptors)).

> **Token de autenticação vai via interceptor, nunca montado à mão no datasource.** Um datasource nunca adiciona `Authorization` manualmente num header de request — isso é responsabilidade de um `Interceptor` (`dio.Interceptor`) registrado na lista `interceptors` do `Dio`.

## Cache (`hive_ce` + `flutter_secure_storage`)

`external/datasources/local/` usa `hive_ce` para persistência local não sensível. Cada "coleção" é uma `Box` do Hive, aberta uma vez no bootstrap (`Hive.initFlutter()` + `Hive.openBox<Map>(collection)` para cada box usada) antes do `Locator.setup()` — nunca aberta sob demanda dentro de um datasource.

```dart
final box = Hive.box<Map>('auth');
await box.put('user', json);
final json = box.get('user');
```

Dado sensível (ex.: token JWT) usa `FlutterSecureStorage` direto, nunca uma `Box` regular:

```dart
final storage = const FlutterSecureStorage();
await storage.write(key: 'token', value: token);
final token = await storage.read(key: 'token');
```

`hasDataInKey`/`delete`/`clear` seguem a API nativa de cada pacote (`box.containsKey`/`box.delete`/`box.clear`, `storage.containsKey`/`storage.delete`/`storage.deleteAll`).

## `Either`/`Failure` (implementação própria do projeto)

Sem `dartz`. `core/either/either.dart` define o tipo próprio:

```dart
sealed class Either<L, R> {
  const Either();
}

final class Left<L, R> extends Either<L, R> {
  final L value;
  const Left(this.value);
}

final class Right<L, R> extends Either<L, R> {
  final R value;
  const Right(this.value);
}

extension EitherX<L, R> on Either<L, R> {
  T fold<T>(T Function(L left) onLeft, T Function(R right) onRight) => switch (this) {
    Left(value: final l) => onLeft(l),
    Right(value: final r) => onRight(r),
  };

  bool isLeft() => this is Left<L, R>;
  bool isRight() => this is Right<L, R>;
}
```

Repository sempre retorna `Either<Failure, T>` — `Left` para falha, `Right` para sucesso. Consumido via `fold`, exatamente como antes:

```dart
result.fold(
  (failure) => emit(LoginFailureState(failure.message)),
  (user) => emit(LoginSuccessState(user)),
);
```

`Failure` (`core/errors/failure.dart`) é a interface base do projeto:

```dart
abstract interface class Failure {
  String get message;
  String? get stackTrace;
}
```

Falhas de módulo implementam `Failure` (`implements`, nunca `extends` — ver [naming_conventions.md](naming_conventions.md)). `RequestFailure` (`core/errors/request_failure.dart`) é a falha genérica de requisição HTTP, própria do projeto:

```dart
final class RequestFailure implements Failure {
  final String message;
  final int? statusCode;
  final String? stackTrace;

  const RequestFailure({required this.message, this.statusCode, this.stackTrace});
}
```

Exceções lançadas por `external/` também são próprias do projeto, em `core/errors/exceptions.dart` (`RequestException`, `CacheException`) — `infrastructure/repositories/` captura essas exceções (nunca `DioException` diretamente) e converte para `Failure`.

## Validators (formulário)

Sem pacote externo de validação. `shared/validators/` tem as classes próprias do projeto, cada uma com um método `call(T? value)` que retorna `String?` (mensagem de erro em português, ou `null` se válido) — compatível com `FormFieldValidator` do Flutter:

```dart
final class RequiredValidator<T> {
  const RequiredValidator();

  String? call(T? value) {
    if (value == null || (value is String && value.trim().isEmpty)) {
      return 'Campo obrigatório';
    }
    return null;
  }
}
```

Implemente cada validator sob demanda (`EmailValidator`, `RequiredValidator<T>` etc.) — nunca regex/checagem manual reescrita direto no widget/bloc.

## DI (`get_it`)

`get_it` é usado diretamente — sem wrapper/abstração própria em cima dele. Documentado em detalhe em [architecture.md](architecture.md#di-injeção-de-dependência).

## Rotas e Design System

`go_router` é dependência direta do projeto (ver [architecture.md](architecture.md#rotas)).

Componentes visuais: **Material 3 nativo do Flutter** (`MaterialApp`, widgets do `package:flutter/material.dart`), tema centralizado via `ThemeData` em `core/theme/`. Antes de criar um widget do zero em `presentation/widgets/`, verifique se já existe um widget Material equivalente (`ElevatedButton`, `TextField`, `Card`, `AlertDialog`, `BottomSheet`, etc.) ou um widget já construído em outro módulo do projeto — nunca duplique um componente que já existe.

## Log

`core/utils/log.dart` define um wrapper próprio e pequeno em cima de `dart:developer` (`log()`) ou `debugPrint` — nunca `print` nem `debugPrint` direto no restante do código:

```dart
abstract final class Log {
  static void info(String message) => developer.log(message, name: 'INFO');
  static void success(String message) => developer.log(message, name: 'SUCCESS');
  static void warning(String message) => developer.log(message, name: 'WARNING');
  static void error(String message, [Object? error, StackTrace? stackTrace]) =>
      developer.log(message, name: 'ERROR', error: error, stackTrace: stackTrace);
}
```
