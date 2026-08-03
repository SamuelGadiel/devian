# Devian

Pipeline de build Flutter (via FVM) com artefatos.

## Como funciona

- O workflow clona o app a partir do Bitbucket (repo privado `branef/sisvisa-serr-mobile`) usando uma deploy key.
- Instala o Flutter via **FVM** (versão fixada no `.fvmrc` do app).
- Usa **cache** do diretório de versões do FVM e do pub-cache para não rebaixar o SDK a cada execução.
- Gera o APK release e publica como **artifact** na aba Actions.

## Rodar manualmente

1. Abra a aba **Actions**
2. Selecione o workflow **Build Flutter APK**
3. **Run workflow** → branch `main`

## Secrets necessários

| Secret | Descrição |
|---|---|
| `BITBUCKET_SSH_KEY` | Chave privada SSH (`id_rsa`) com acesso ao repo `branef/sisvisa-serr-mobile` no Bitbucket — a mesma usada no container `devian`, já configurada no GitHub e Bitbucket |

## Estrutura

```
.github/workflows/build.yml   # workflow de build
app/                          # criado em runtime pelo clone do Bitbucket (não versionado aqui)
```
