from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# --- Projetos ---
class ProjetoCreate(BaseModel):
    nome: str = Field(min_length=1, max_length=100)
    repo_url: str | None = None
    branch_padrao: str = "main"
    caminho_container: str | None = None


class ProjetoUpdate(BaseModel):
    nome: str | None = Field(default=None, min_length=1, max_length=100)
    repo_url: str | None = None
    branch_padrao: str | None = None
    caminho_container: str | None = None


class ProjetoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    repo_url: str | None
    branch_padrao: str
    caminho_container: str | None
    criado_em: datetime


# --- Chats ---
class ChatCreate(BaseModel):
    projeto_id: int
    name: str | None = Field(default=None, max_length=100)


class ChatRename(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class ChatOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    projeto_id: int
    name: str
    branch: str
    status: str
    criada_em: datetime
    atualizada_em: datetime


# --- Mensagens ---
class MensagemCreate(BaseModel):
    conteudo: str = Field(min_length=1)


class MensagemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str
    conteudo: str
    criada_em: datetime


class MensagemPage(BaseModel):
    mensagens: list[MensagemOut]
    next_cursor: int | None


# --- Artefatos ---
class ArtefatoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome_arquivo: str
    tamanho: int
    content_type: str | None
    criado_em: datetime
