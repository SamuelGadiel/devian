from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ChatRequest(BaseModel):
    chat_id: str
    mensagem: str
    projeto: str | None = None
    branch: str = "main"


class ChatResponse(BaseModel):
    chat_id: str
    session_id: str
    resposta: str


class MensagemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str
    conteudo: str
    criada_em: datetime


class SessaoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    chat_id_app: str
    session_id_claude: str
    branch: str
    status: str
    criada_em: datetime


class SessaoDetalhe(SessaoOut):
    mensagens: list[MensagemOut] = []


class ProjetoCreate(BaseModel):
    nome: str
    repo_url: str
    branch_padrao: str = "main"


class ProjetoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    repo_url: str
    branch_padrao: str
    criado_em: datetime
