from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

# ============================================================
# Projetos
# ============================================================


class ProjetoCreate(BaseModel):
    """Cria um projeto a partir de um repositório EXISTENTE."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "nome": "sisvisa",
                    "repo_url": "git@bitbucket.org:branef/sisvisa-serr-mobile.git",
                    "branch_padrao": "main",
                    "caminho_container": "/workspace/sisvisa-serr-mobile",
                }
            ]
        }
    )

    nome: str = Field(
        min_length=1,
        max_length=100,
        description="Nome curto do projeto. Vira o identificador único.",
        examples=["sisvisa"],
    )
    repo_url: str | None = Field(
        default=None,
        description="URL do repositório existente (git@ ou https://).",
        examples=["git@bitbucket.org:branef/sisvisa-serr-mobile.git"],
    )
    branch_padrao: str = Field(
        default="main",
        description="Branch usada por padrão nos builds.",
        examples=["main"],
    )
    caminho_container: str | None = Field(
        default=None,
        description=(
            "Diretório dentro do container `devian` onde o Claude Code roda. "
            "Faz o Claude carregar a camada do projeto (CLAUDE.md / .claude)."
        ),
        examples=["/workspace/sisvisa-serr-mobile"],
    )


class ProjetoUpdate(BaseModel):
    """Atualização parcial — só envia os campos que quer mudar."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "branch_padrao": "develop",
                }
            ]
        }
    )

    nome: str | None = Field(default=None, min_length=1, max_length=100)
    repo_url: str | None = None
    branch_padrao: str | None = None
    caminho_container: str | None = None


class ProjetoOut(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": 1,
                    "nome": "sisvisa",
                    "repo_url": "git@bitbucket.org:branef/sisvisa-serr-mobile.git",
                    "branch_padrao": "main",
                    "caminho_container": "/workspace/sisvisa-serr-mobile",
                    "criado_em": "2026-08-04T21:44:03.305361Z",
                }
            ]
        },
    )

    id: int
    nome: str
    repo_url: str | None
    branch_padrao: str
    caminho_container: str | None
    criado_em: datetime


# ============================================================
# Chats
# ============================================================


class ChatCreate(BaseModel):
    """Abre um chat novo dentro de um projeto."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "projeto_id": 1,
                    "name": "nova-feature",
                }
            ]
        }
    )

    projeto_id: int = Field(
        description="Id do projeto ao qual o chat pertence.",
        examples=[1],
    )
    name: str | None = Field(
        default=None,
        max_length=100,
        description=(
            "Nome/slug do chat. Se omitido, nasce 'novo-chat' e vira o slug "
            "da primeira mensagem (ex: 'qual-a-cor')."
        ),
        examples=["nova-feature"],
    )


class ChatRename(BaseModel):
    """Renomeia o name (slug) exibido no drawer."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "name": "ajuste-no-relatorio",
                }
            ]
        }
    )

    name: str = Field(min_length=1, max_length=100)


class ChatOut(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": 1,
                    "projeto_id": 1,
                    "name": "qual-a-cor",
                    "branch": "main",
                    "status": "ativa",
                    "criada_em": "2026-08-04T21:44:08.958822Z",
                    "atualizada_em": "2026-08-04T21:44:12.366232Z",
                }
            ]
        },
    )

    id: int
    projeto_id: int
    name: str
    branch: str
    status: str
    criada_em: datetime
    atualizada_em: datetime


# ============================================================
# Mensagens
# ============================================================


class MensagemCreate(BaseModel):
    """A próxima mensagem do usuário. Só isso — nada de histórico no payload."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "conteudo": "Pode adicionar um botão de exportar PDF no relatório?",
                }
            ]
        }
    )

    conteudo: str = Field(
        min_length=1,
        description="Texto da mensagem enviada à assistente.",
    )


class MensagemOut(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": 4,
                    "role": "assistant",
                    "conteudo": "Claro! Adicionei um botão de exportar PDF no rodapé do relatório.",
                    "criada_em": "2026-08-04T21:44:12.366232Z",
                }
            ]
        },
    )

    id: int
    role: str = Field(description="'user' ou 'assistant'")
    conteudo: str
    criada_em: datetime


class MensagemPage(BaseModel):
    """Página do histórico. `next_cursor` = id da msg mais antiga desta página;
    passe-o como `cursor` na próxima chamada para buscar as anteriores
    (scroll para cima). `null` = chegou ao início da conversa."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "mensagens": [
                        {
                            "id": 4,
                            "role": "assistant",
                            "conteudo": "Claro! Feito.",
                            "criada_em": "2026-08-04T21:44:12.366232Z",
                        },
                        {
                            "id": 3,
                            "role": "user",
                            "conteudo": "Pode adicionar um botão de exportar PDF?",
                            "criada_em": "2026-08-04T21:44:12.361597Z",
                        },
                    ],
                    "next_cursor": 3,
                }
            ]
        }
    )

    mensagens: list[MensagemOut]
    next_cursor: int | None


# ============================================================
# Artefatos
# ============================================================


class ArtefatoOut(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": 1,
                    "nome_arquivo": "serr-homolog-0.1.0(1).apk",
                    "tamanho": 29413656,
                    "content_type": "application/vnd.android.package-archive",
                    "criado_em": "2026-08-04T21:44:36.951372Z",
                }
            ]
        },
    )

    id: int
    nome_arquivo: str
    tamanho: int = Field(description="Tamanho em bytes")
    content_type: str | None
    criado_em: datetime
