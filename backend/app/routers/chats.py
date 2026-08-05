import re
import unicodedata
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import require_token
from app.db import get_db
from app.services.claude import ClaudeError, ClaudeTimeout, run_claude

router = APIRouter(prefix="/chats", tags=["chats"])

UNAUTHORIZED = {401: {"description": "Token Bearer ausente ou inválido"}}
NOT_FOUND = {404: {"description": "Chat ou projeto não encontrado"}}
VALIDATION = {422: {"description": "Corpo da requisição inválido"}}
CLAUDE_ERROR = {502: {"description": "Erro do Claude Code no container (ClaudeError)"}}
CLAUDE_TIMEOUT = {504: {"description": "O Claude Code não respondeu a tempo (timeout)"}}


def slugify(texto: str, max_len: int = 50) -> str:
    """Gera um slug legível a partir de um texto (ex: 'Qual a cor?' -> 'qual-a-cor')."""
    texto = unicodedata.normalize("NFKD", texto)
    texto = texto.encode("ascii", "ignore").decode("ascii")
    texto = texto.lower()
    texto = re.sub(r"[^a-z0-9]+", "-", texto).strip("-")
    return texto[:max_len].strip("-") or "conversa"


def _get_chat_or_404(db: Session, chat_id: int) -> models.Chat:
    chat = db.get(models.Chat, chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat não encontrado")
    return chat


@router.get(
    "",
    response_model=list[schemas.ChatOut],
    summary="Listar chats",
    response_description="Chats do projeto (ou todos), mais recentes primeiro",
    responses={**UNAUTHORIZED},
)
def listar_chats(
    projeto_id: int | None = Query(
        default=None,
        description="Se informado, filtra chats do projeto",
        examples=[1],
    ),
    db: Session = Depends(get_db),
    _=Depends(require_token),
):
    q = db.query(models.Chat)
    if projeto_id is not None:
        q = q.filter_by(projeto_id=projeto_id)
    return q.order_by(models.Chat.atualizada_em.desc()).all()


@router.post(
    "",
    response_model=schemas.ChatOut,
    status_code=201,
    summary="Criar chat",
    response_description="Chat criado (name vira slug da 1ª mensagem se omitido)",
    responses={**UNAUTHORIZED, **NOT_FOUND, **VALIDATION},
)
def criar_chat(
    req: schemas.ChatCreate,
    db: Session = Depends(get_db),
    _=Depends(require_token),
):
    if not db.get(models.Projeto, req.projeto_id):
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    chat = models.Chat(
        projeto_id=req.projeto_id,
        name=req.name or "novo-chat",
        session_id_claude=str(uuid4()),
    )
    db.add(chat)
    db.commit()
    db.refresh(chat)
    return chat


@router.get(
    "/{chat_id}",
    response_model=schemas.ChatOut,
    summary="Obter chat",
    response_description="Detalhes do chat",
    responses={**UNAUTHORIZED, **NOT_FOUND},
)
def obter_chat(
    chat_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_token),
):
    return _get_chat_or_404(db, chat_id)


@router.delete(
    "/{chat_id}",
    status_code=204,
    summary="Deletar chat",
    response_description="Chat e histórico deletados (mensagens em cascata)",
    responses={**UNAUTHORIZED, **NOT_FOUND},
)
def deletar_chat(
    chat_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_token),
):
    chat = _get_chat_or_404(db, chat_id)
    db.delete(chat)
    db.commit()


@router.put(
    "/{chat_id}/rename",
    response_model=schemas.ChatOut,
    summary="Renomear chat",
    response_description="Chat renomeado",
    responses={**UNAUTHORIZED, **NOT_FOUND, **VALIDATION},
)
def renomear_chat(
    chat_id: int,
    req: schemas.ChatRename,
    db: Session = Depends(get_db),
    _=Depends(require_token),
):
    chat = _get_chat_or_404(db, chat_id)
    chat.name = req.name
    db.commit()
    db.refresh(chat)
    return chat


@router.get(
    "/{chat_id}/mensagens",
    response_model=schemas.MensagemPage,
    summary="Histórico do chat (paginado)",
    response_description=(
        "Página de mensagens em ordem cronológica. Sem `cursor` → as "
        "**mais recentes**; com `cursor` → as anteriores àquele id (scroll p/ cima). "
        "`next_cursor: null` = início da conversa."
    ),
    responses={**UNAUTHORIZED, **NOT_FOUND},
)
def listar_mensagens(
    chat_id: int,
    cursor: int | None = Query(
        default=None,
        description=(
            "Id da mensagem mais antiga da página atual. Passe o `next_cursor` "
            "retornado para buscar as anteriores."
        ),
        examples=[42],
    ),
    limit: int = Query(
        default=50,
        ge=1,
        le=200,
        description="Quantidade de mensagens por página (1–200)",
        examples=[50],
    ),
    db: Session = Depends(get_db),
    _=Depends(require_token),
):
    q = db.query(models.Mensagem).filter_by(chat_id=chat_id)
    if cursor is not None:
        q = q.filter(models.Mensagem.id < cursor)
    msgs = q.order_by(models.Mensagem.id.desc()).limit(limit).all()
    msgs.reverse()  # ordem cronológica pra exibição
    next_cursor = msgs[0].id if len(msgs) == limit else None
    return schemas.MensagemPage(mensagens=msgs, next_cursor=next_cursor)


@router.post(
    "/{chat_id}/mensagens",
    response_model=schemas.MensagemOut,
    status_code=201,
    summary="Enviar mensagem",
    response_description=(
        "Mensagem do usuário gravada, processada pelo Claude Code na sessão do "
        "chat e resposta do assistente gravada e retornada. Payload leve: "
        "**só a última mensagem** — o contexto fica na sessão + no banco."
    ),
    responses={**UNAUTHORIZED, **NOT_FOUND, **VALIDATION, **CLAUDE_ERROR, **CLAUDE_TIMEOUT},
)
def enviar_mensagem(
    chat_id: int,
    req: schemas.MensagemCreate,
    db: Session = Depends(get_db),
    _=Depends(require_token),
):
    chat = _get_chat_or_404(db, chat_id)
    primeira = not db.query(models.Mensagem).filter_by(chat_id=chat.id).first()

    db.add(models.Mensagem(chat_id=chat.id, role="user", conteudo=req.conteudo))
    db.commit()

    try:
        resposta = run_claude(
            req.conteudo,
            chat.session_id_claude,
            resume=not primeira,
            workdir=chat.projeto.caminho_container if chat.projeto else None,
        )
    except ClaudeTimeout as exc:
        raise HTTPException(status_code=504, detail=str(exc)) from exc
    except ClaudeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    db.add(models.Mensagem(chat_id=chat.id, role="assistant", conteudo=resposta))
    if chat.name == "novo-chat":
        chat.name = slugify(req.conteudo)
    db.commit()

    return db.query(models.Mensagem).order_by(models.Mensagem.id.desc()).first()
