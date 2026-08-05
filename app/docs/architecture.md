# Arquitetura

Clean Architecture organizada por **módulos**. Cada módulo é dividido em até 4 camadas. Este documento descreve o que cada camada faz, o que não pode fazer, e como elas se relacionam.

## Camadas

Um módulo pode ter até 4 camadas — **não são todas obrigatórias** (ver [Módulos](#módulos) mais adiante). Quando existem, seguem estritamente estas responsabilidades:

### `domain/`

A regra de negócio pura do módulo. Não conhece Flutter, Dio, Hive, nem qualquer outra dependência externa — só Dart puro (e o `Either`/`Failure` do próprio projeto, em `core/`, que são abstrações neutras — ver [dependencies_usage.md](dependencies_usage.md#eitherfailure-implementação-própria-do-projeto)).

Contém:

- `entities/` — objetos de negócio (ex.: `User`). Carregam validação/lógica própria quando fizer sentido (ex.: uma entidade pode ter um método que valida se está em estado consistente).
- `repositories/` — só a interface (contrato). Nunca a implementação — isso mora em `infrastructure/`.
- `usecases/` — uma ação de negócio por arquivo, com **abstração + implementação no mesmo arquivo**: abstração é o verbo puro (`Login`, não `LoginUsecase` — ver [naming_conventions.md](naming_conventions.md)), implementação é o mesmo nome + `Implementation` (`LoginImplementation`). Método único `call()`. Recebe/retorna entidades, nunca JSON ou Mapper.
- `failures/` — `Failure`s específicos do módulo, implementando o `Failure` base do projeto (`core/errors/failure.dart`).

**Nunca**: importa `infrastructure/`, `external/` ou `presentation/` — nem do próprio módulo, nem de outro.

> **Por que usecase tem abstração + implementação no mesmo arquivo (e não em camadas separadas, como repository)?** Repository/datasource cruzam uma fronteira arquitetural de verdade (quem consome não é quem implementa — `domain` consome, `infrastructure` implementa). Usecase não tem essa fronteira: a implementação da regra de negócio **é** o `domain`, não existe uma "camada de baixo" que a implemente. A abstração existe só para permitir mockar o usecase em teste de Bloc (via `mocktail`) — por isso as duas ficam juntas, no mesmo lugar.

### `infrastructure/`

Implementa os contratos definidos em `domain/`. É a camada que sabe orquestrar `external/` e converter dado bruto em entidade — **é sempre quem chama o Mapper**, nas duas direções.

Contém:

- `repositories/` — só a implementação: `<Nome>RepositoryImplementation`, implementa a interface de `domain/repositories/`. Chama `external/` (datasources), converte `Exception → Failure` (try/catch) e `JSON ↔ Entity` (via Mapper).
- `datasources/` — só a **abstração** (interface) dos datasources que `external/` vai implementar (ex.: `AuthRemoteDatasource`, `AuthLocalDatasource`). `infrastructure/repositories/` é quem consome o datasource, então é aqui que o contrato mora — mesma lógica de `domain/repositories/` guardar a abstração que `infrastructure` implementa.
- `mappers/` — `<Entidade>Mapper`, classe com métodos estáticos (`toJson`/`fromJson`, ou `toLocalJson`/`toRemoteJson`/`fromLocalJson`/`fromRemoteJson` quando local e remoto divergem). Só converte, sem lógica — lógica fica na entidade.

**Nunca**: contém regra de negócio (isso é papel do `domain/`); nunca é chamada diretamente por `presentation/` (sempre via `domain/usecases/`).

#### Direção do dado: quem monta o JSON?

**O repository (`infrastructure/`), nunca o datasource (`external/`).** `external/` só enxerga `Map<String, dynamic>`/primitivos — nunca `Entity` nem `Mapper` (ver seção abaixo).

- **Enviando dado** (ex.: criar/atualizar algo): o repository chama `Mapper.toJson(entity)` (ou `toRemoteJson`) para gerar o `Map<String, dynamic>`, e passa esse mapa pronto pro método do datasource. O datasource só repassa esse mapa pro `DioClient`/`CacheService` — nunca recebe a `Entity`.
- **Recebendo dado** (ex.: resposta de login, leitura de cache): o datasource retorna o `Map<String, dynamic>` cru (ou lança `Exception`); o repository chama `Mapper.fromJson(json)` (ou `fromRemoteJson`/`fromLocalJson`) pra transformar esse mapa em `Entity`.

Nem toda operação usa as duas direções — no login, por exemplo, a entrada é só `email`/`senha` (primitivos, sem `Entity` envolvida em enviar), mas a resposta do backend (token/dados do usuário) usa `UserMapper.fromRemoteJson()` pra virar `User`.

### `external/`

Acesso bruto a dado — API e cache. Não conhece `Entity`, `Mapper` nem `Either`/`Failure`. Só recebe/retorna dado (`Map<String, dynamic>`/primitivos) ou lança uma `Exception`.

Contém:

- `datasources/remote/` — só a **implementação** da abstração definida em `infrastructure/datasources/` (ex.: `AuthRemoteDatasourceImplementation implements AuthRemoteDatasource`). Usa o `Dio` diretamente.
- `datasources/local/` — mesmo esquema, usando `hive_ce` (Hive), ou `flutter_secure_storage` quando o dado for sensível — ex.: token (ver [dependencies_usage.md](dependencies_usage.md#cache-hive_ce--flutter_secure_storage)).

**Nunca**: referencia `Mapper` ou `Entity` — isso é papel do `infrastructure/`. `external/` só cuida da requisição/leitura em si, sempre com JSON bruto ou primitivos entrando e saindo. **Nunca** define a abstração do datasource — só implementa a que `infrastructure/` já definiu.

#### Endpoint nunca é string literal — sempre `ApiRoutes`

Todo endpoint passado ao `Client`/`DioClient` (`get`, `post`, `put`, `patch`, `delete`, `request`) vem de uma constante estática da classe `ApiRoutes`, agregador único e global em `core/network/api_routes.dart` — mesmo raciocínio de `Routes` para navegação, aplicado a rotas de API.

```dart
// core/network/api_routes.dart
abstract final class ApiRoutes {
  static const String login = '/login';
}

// modules/auth/external/datasources/remote/auth_remote_datasource_implementation.dart
final response = await client.post(ApiRoutes.login, body: {'email': email, 'password': password});
```

### `presentation/`

UI e orquestração de estado da tela.

Contém:

- `blocs/<nome>_bloc/` — uma pasta por Bloc, com 3 arquivos: `<nome>_bloc.dart`, `<nome>_events.dart` (sealed `<Nome>Events`), `<nome>_states.dart` (sealed `<Nome>States`). Chama `usecases` de `domain/` (do próprio módulo ou de outro — ver [Boundaries](#boundaries-entre-módulos)). **Nunca** chama outro Bloc.
- `pages/` — telas (`<Nome>Page`), consomem o Bloc via `BlocBuilder`/`BlocListener`/`BlocConsumer`.
- `widgets/` — componentes de UI específicos do módulo.

**Nunca**: chama `usecase`, `repository` ou `datasource` diretamente — sempre via Bloc.

#### Um Bloc por fluxo coerente (não por módulo, nem por ação)

Um Bloc emite **um único estado atual**. Se dois fluxos de um módulo puderem estar "ativos" ao mesmo tempo na tela — ex.: uma tela mostrando dados de sucesso do fluxo A, e em paralelo um evento do fluxo B dispara um `Loading` no mesmo Bloc —, o novo estado sobrescreve o anterior e a UI perde a informação do fluxo A. **Esse é o problema a evitar, sempre.**

- Se as ações de um módulo são **mutuamente exclusivas** (nunca ocorrem ao mesmo tempo, uma não depende do estado da outra) — ex.: login, recuperar senha e logout do módulo Auth —, elas podem conviver no mesmo Bloc: `AuthBloc`/`AuthEvents`/`AuthStates`, com `LoginEvent`, `RecoverPasswordEvent`, `LogoutEvent` como cases.
- Se um módulo tem fluxos que **podem coexistir na tela** (dois dados exibidos e atualizados de forma independente), cada fluxo vira um Bloc separado — do contrário, o estado de um é perdido quando o outro emite.
- Se um Bloc cresce demais em número de estados mas continua sendo um único fluxo coerente, dá pra segmentar sem criar um Bloc novo: um `<Sub>States` que implementa/estende o `States` do Bloc principal, representando um subconjunto do fluxo.
- **Essa decisão é avaliada caso a caso, na hora de implementar** — não existe regra fixa de granularidade. O nome do Bloc (`<Nome>Bloc`/`<Nome>Events`/`<Nome>States`) reflete o que foi decidido: pode ser o nome do módulo (`AuthBloc`) ou de uma ação específica (`CheckoutBloc` isolado de outro fluxo que precisa coexistir na mesma tela), conforme o critério acima.

## Fluxo de dependência

```
presentation → domain ← infrastructure → external
```

`domain` é o centro: `presentation` depende dele (via usecase), `infrastructure` depende dele (implementa a interface). `domain` não depende de nada — nem de `infrastructure`, nem de `external`, nem de `presentation`, nem do próprio Flutter.

---

## Módulos

Um **módulo** é uma unidade de fluxo de negócio — não uma tela, não uma camada, não um arquivo. Ex.: `Auth` é um módulo (engloba login, recuperar senha, logout); `Home` é outro módulo (hub de navegação). **Não existem submódulos** — um módulo não contém outro módulo dentro dele.

Cada módulo vive em `lib/modules/<module>/` e contém **só as camadas que ele precisa** entre `domain/`, `infrastructure/`, `external/`, `presentation/` — as 4 camadas descritas acima são o conjunto disponível, não uma obrigação. Não existe arquivo solto na raiz do módulo (nada de `module.dart`, `_exports.dart` ou fachada de qualquer tipo) — só as pastas de camada que fizerem sentido para aquele módulo.

### Módulo cresce incrementalmente

Um módulo nasce com o mínimo necessário e ganha camadas conforme passa a ter razão de existir para elas:

- **Módulo com regra de negócio real** (busca dado, valida, decide) — ex.: `Auth` — tem as 4 camadas desde o início: `domain` (entidade, repository abstração, usecase abstração+implementação, failure), `infrastructure` (repository implementação, datasource abstração, mapper), `external` (datasource implementação), `presentation` (bloc, page).
- **Módulo puramente visual/de orquestração** (sem dado próprio, sem regra de negócio) — ex.: `Home`, no escopo atual — pode nascer só com `presentation/` (uma `HomePage` em branco). Não faz sentido criar `domain/failures/` vazia só para "seguir o padrão".
- Se, mais tarde, `Home` precisar buscar dados (ex.: um resumo do usuário), aí sim ganha `domain/`, `infrastructure/`, `external/` — incrementando o módulo existente, nunca recriando.

### O que NÃO muda, independente de quantas camadas o módulo tem

- **DI e rotas nunca moram dentro do módulo.** Ficam em `core/service_locator/binds/<module>_binds.dart` e `core/router/routes/<module>_routes.dart`. Um módulo só-`presentation` ainda registra sua página no `core/router/`, mesmo sem ter bind nenhum pra registrar (nesse caso, o módulo simplesmente não tem arquivo em `binds/`).
- **A regra de boundary entre módulos** (ver próxima seção) vale igual, tenha o módulo 1 camada ou 4.

---

## `shared/`

Pasta plana (sem subpastas de camada) para artefatos genuinamente reutilizáveis por qualquer módulo, sem lógica de negócio de um fluxo específico.

**Pode morar em `shared/`:**

- `Failure`s genéricas, não ligadas à regra de negócio de nenhum módulo (ex.: `CacheFailure`, `UnexpectedFailure`, em `shared/failures/`) — diferente de uma failure como `InvalidCredentialsFailure`, que é específica do `Auth` e mora em `domain/failures/` do próprio módulo.
- Páginas/widgets sem dono de negócio (ex.: uma `PlaceholderPage` usada antes de qualquer módulo existir, em `shared/presentation/pages/`).

**Não pode morar em `shared/`:**

- Nada que pertença à regra de negócio de um módulo específico — isso é `domain`/`presentation` do próprio módulo, mesmo que pareça "genérico" à primeira vista.
- Entidade, usecase, repository ou Bloc de um fluxo de negócio — mesmo compartilhado entre módulos, o lugar certo é o `domain` do módulo dono do fluxo (que qualquer outro módulo pode importar livremente, ver [Boundaries](#boundaries-entre-módulos)).

Na dúvida: se o artefato só existe por causa de uma regra de negócio de um módulo, ele mora no módulo. Se existiria do mesmo jeito mesmo que nenhum módulo de negócio tivesse sido criado ainda, mora em `shared/`.

---

## Interceptors (`core/network/interceptors/`)

Interceptors HTTP customizados (ex.: injeção de token, refresh automático de sessão) não pertencem a nenhum módulo de negócio — são infraestrutura transversal, consumida por qualquer módulo que use o `Dio` injetado. Vivem em `core/network/interceptors/`, implementam `dio.Interceptor`, são registrados em `CoreBinds` (`core/service_locator/binds/core_binds.dart`) e injetados na lista `interceptors` da instância de `Dio` montada em `core/network/dio_client.dart`.

Regra de dependência: um interceptor pode depender de `domain/` (entidades, usecases, repositories) de qualquer módulo — mesma regra de "`domain` cruza módulo livremente" já usada por `presentation`/bootstrap (ex.: `HasActiveSession` consumido direto pelo `main.dart`). Um interceptor **nunca** depende de `infrastructure/`/`external/` de um módulo diretamente — só do contrato estável (`domain`).

> **Atenção ao `validateStatus` do `Dio`:** a instância de `Dio` em `core/network/dio_client.dart` sempre configura `validateStatus: (status) => true` — nenhum status HTTP (401, 400, 500...) lança `DioException` nesta stack. Um interceptor que precisa reagir a um status de erro específico faz isso em `onResponse` (checando `response.statusCode`), nunca em `onError` (que só recebe falhas reais de conexão — timeout, sem rede). Todo datasource remoto segue a mesma lógica: checa `response.statusCode` manualmente e lança a exceção correspondente (ver [dependencies_usage.md](dependencies_usage.md#http-dio)) — `Dio` nunca lança por conta de um status HTTP.

---

## Boundaries entre módulos

Regra resumida: **`domain` cruza módulo livremente; `infrastructure` e `external` nunca cruzam; um Bloc pode chamar vários usecases (do próprio módulo ou de outro), mas nunca outro Bloc; `presentation` pode compor Blocs de módulos diferentes na mesma tela.**

### `domain` pode ser importado direto de outro módulo

`domain` já é o contrato estável de um módulo — não conhece Flutter, Dio, Hive, nem detalhe de implementação. Por isso, um módulo pode importar `entities/`, `usecases/` (a abstração) ou `repositories/` (a interface) de outro módulo diretamente, sem indireção nenhuma (sem fachada, sem `_exports.dart`).

Exemplo: o módulo `Home` pode importar `modules/auth/domain/usecases/get_current_user.dart` pra saber quem é o usuário logado, sem precisar duplicar nada.

### `infrastructure` e `external` NUNCA cruzam módulo

Um módulo nunca importa `infrastructure/` ou `external/` de outro módulo. Esses são detalhes de implementação — se `Home` precisa de dado que hoje mora na `infrastructure`/`external` do `Auth`, o caminho correto é `Home` chamar o `usecase` do `Auth` (que já orquestra tudo isso por trás), nunca pular direto pro repository ou datasource.

### Bloc nunca chama outro Bloc

Isso vale **mesmo dentro do mesmo módulo** — não é uma regra só de fronteira entre módulos. Um Bloc não guarda referência a outro Bloc nem reage a mudanças de outro Bloc diretamente. Um Bloc orquestra **usecases** (do próprio módulo ou de outro, já que `domain` cruza módulo livremente) — nunca outro Bloc. Isso evita acoplamento oculto e rebuilds em cascata difíceis de rastrear (é o mesmo motivo pelo qual a documentação oficial do pacote `bloc` desaconselha comunicação Bloc-a-Bloc, independente de módulo).

### `presentation` pode compor Blocs de módulos diferentes

Uma tela (`Page`) pode usar múltiplos `BlocBuilder`/`BlocListener`/`BlocConsumer` com Blocs de módulos diferentes — ex.: uma `HomePage` mostrando dado do `AuthBloc` (usuário logado) e de um futuro `OrdersBloc`. **Não usamos `MultiBlocProvider`** — só `BlocBuilder`, `BlocListener` ou `BlocConsumer`, um por Bloc, tantos quantos a tela precisar. Isso **não é** um módulo "acessando" o outro — é composição de tela, que é o papel natural da camada de apresentação. O que não pode é um módulo instanciar/chamar o Bloc de outro módulo por baixo dos panos (fora do contexto de composição da própria tela).

### Enforcement

Não há lint ou script automático verificando esses boundaries — a checagem é feita pelo agente QA em toda validação (ver `.claude/agents/qa.md`).

---

## DI (Injeção de Dependência)

Usamos `get_it` diretamente (`GetIt.instance`) — sem wrapper/abstração própria em cima dele.

### Cada módulo tem um Binds — fora do módulo

Um módulo que precisa registrar algo (datasource, repository, usecase, Bloc) tem um arquivo `<module>_binds.dart`, mas ele **mora em `core/service_locator/binds/`, não dentro do módulo** (ver [Módulos](#o-que-não-muda-independente-de-quantas-camadas-o-módulo-tem)). A classe registra tudo **dentro do próprio construtor** — sem um método `register()` separado:

```dart
final class AuthBinds {
  AuthBinds() {
    GetIt.instance.registerLazySingleton<AuthRemoteDatasource>(() => AuthRemoteDatasourceImplementation(GetIt.instance()));
    GetIt.instance.registerLazySingleton<AuthRepository>(() => AuthRepositoryImplementation(GetIt.instance()));
    GetIt.instance.registerLazySingleton<Login>(() => LoginImplementation(GetIt.instance()));
    GetIt.instance.registerLazySingleton<AuthBloc>(() => AuthBloc(GetIt.instance()));
  }
}
```

Um módulo puramente `presentation` (ex.: `Home`, sem nada pra injetar) simplesmente **não tem arquivo em `binds/`** — não existe `HomeBinds` vazio só pra existir.

### Convenção de lifecycle

**Tudo é `registerLazySingleton` por padrão** — só usamos outra coisa (`registerFactory`, `registerSingleton`) quando há uma razão concreta pra isso. Vale pra datasources, repositories, usecases **e Blocs**: um Bloc como `lazySingleton` mantém o estado do fluxo quando o usuário sai e volta pra tela (não perde o que já tinha carregado), diferente de `factory`, que recriaria o Bloc do zero a cada navegação.

### Agregador único: `core/service_locator/locator.dart`

Uma classe que só instancia os `Binds` de todos os módulos, na ordem que fizer sentido, e expõe o único ponto de leitura usado fora do próprio `get_it`:

```dart
abstract final class Locator {
  static T get<T extends Object>() => GetIt.instance<T>();

  static Future<void> setup() async {
    AuthBinds();
    // próximos módulos entram aqui conforme forem criados
  }
}
```

Chamado uma vez, no `main.dart`, antes do `runApp`.

### Como consumir

`Locator.get<T>()` só é chamado na camada de apresentação (`Page`/`Widget`) — nunca em `Bloc`, `usecase` ou `repository`, que recebem suas dependências exclusivamente por injeção no construtor. Dentro de `presentation/`, serve para: obter o Bloc da própria tela, compor Bloc de outro módulo na mesma tela (ver [Boundaries](#presentation-pode-compor-blocs-de-módulos-diferentes)), ou obter um serviço simples registrado no `get_it` — nunca `GetIt.instance<T>()` direto fora de `Locator`, nunca instancia a dependência na mão. Ver [Anti-patterns](#anti-patterns) para o motivo.

---

## Anti-patterns

Duas regras cross-cutting, válidas para qualquer módulo, formalizadas aqui para evitar que sejam quebradas por engano.

### `Locator.get<T>()` só em `Page`/`Widget`

`Bloc`, `usecase` e `repository` nunca chamam `Locator.get<T>()` — toda dependência chega por injeção no construtor (via `Binds`) ou por parâmetro de quem já a tem. Só a camada de apresentação (`Page`/`Widget`) usa `Locator.get<T>()`, e apenas para: obter o Bloc da própria tela, compor Bloc de outro módulo na tela (via `BlocBuilder`/`BlocListener`, reagindo a mudança de estado), ou obter um serviço simples registrado no `get_it` (ex.: um wrapper de seleção de arquivo/imagem, se o projeto vier a precisar).

O que não pode: uma `Page`/`Widget` chamar `Locator.get<OutroBloc>().state` de forma imperativa e síncrona, para extrair um dado de negócio e repassá-lo a outro fluxo (ex.: ler o usuário logado no `AuthBloc` para preencher um campo de outro formulário) — isso é diferente de reagir reativamente a uma mudança de estado (permitido). No primeiro caso, o dado deveria vir de um usecase que o usecase consumidor injeta e chama internamente (ver regra seguinte).

### Usecase autossuficiente por composição

Um usecase só recebe por parâmetro o que genuinamente não pode obter por conta própria — dado de negócio específico da ação, informado pelo usuário (texto de formulário, seleção numa tela). Qualquer dado que outro usecase ou repository já saiba fornecer (usuário logado, emergência atual, uma lista de referência) é obtido internamente: o usecase injeta esse outro usecase/repository no construtor e o chama por conta própria. Quem invoca um usecase não precisa saber como ele obtém os dados que usa internamente — um usecase pode orquestrar chamadas a outros usecases livremente (composição/orquestração é o padrão esperado, não uma exceção).

Exemplo já aplicado no projeto: `GetOperationalDaysImplementation` injeta `GetCurrentEmergency` e o chama internamente, em vez de exigir que o Bloc busque a emergência atual e a repasse como parâmetro. Mesmo padrão em `GetCurrentUser`, usado pelos usecases de registro/salvamento para obter o usuário autenticado sem que o Bloc precise ler `AuthBloc.state`.

---

## Rotas

Usamos `go_router`.

### Cada módulo tem um arquivo de rotas — fora do módulo

Mesmo raciocínio do DI: um `<module>_routes.dart` com as `GoRoute` daquele módulo, morando em `core/router/routes/`, nunca dentro do módulo.

Um módulo puramente `presentation` sem lógica (ex.: `Home`) ainda tem seu `home_routes.dart` — toda tela navegável precisa de rota, mesmo sem bind.

### Valor de rota nunca é string literal — sempre `Routes`

Todo `path` — seja na definição do `GoRoute`/`StatefulShellBranch`, seja em qualquer chamada de navegação (`context.go`, `context.push`, `context.replace`) — vem de uma constante estática da classe `Routes`, agregador único e global em `core/router/routes.dart` (arquivo, distinto da pasta `core/router/routes/`, que continua guardando os `GoRoute`s por módulo). Nenhum módulo escreve o path na mão; todos importam e referenciam `Routes.<constante>`.

```dart
// core/router/routes.dart
abstract final class Routes {
  static const String login = '/login';
  static const String home = '/home';
}

// core/router/routes/auth_routes.dart
List<RouteBase> get authRoutes => [
  GoRoute(path: Routes.login, builder: (context, state) => const LoginPage()),
];
```

Alterar o valor de uma rota passa a exigir edição em um único arquivo — nunca busca textual pelo projeto.

### Agregador único: `core/router/router.dart`

Junta as rotas de todos os módulos num `GoRouter` só:

```dart
final GoRouter router = GoRouter(
  initialLocation: '/login',
  routes: [
    ...authRoutes,
    ...homeRoutes,
    // próximos módulos entram aqui conforme forem criados
  ],
);
```

Usado no `main.dart` via `MaterialApp.router(routerConfig: router)`.

### Navegação é responsabilidade da `Page`, nunca do Bloc

O Bloc não conhece `BuildContext` nem `go_router` — ele só emite estado. Quem decide navegar é a `Page`, reagindo a um estado específico dentro de um `BlocListener` (ex.: `LoginSuccessState` → `context.go(Routes.home)`). Isso mantém o Bloc testável sem widget nenhum envolvido.

### Guards (`redirect`)

Ainda não usado (só temos login/home, sem rota que precise bloquear usuário deslogado). Quando for necessário, o parâmetro `redirect` do `GoRouter` resolve isso nativamente, sem precisar de lógica de guard espalhada pelas páginas.
