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


def slugify(text: str, max_len: int = 50) -> str:
    """Gera um slug legível a partir de um texto (ex: 'Qual a cor?' -> 'qual-a-cor')."""
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text[:max_len].strip("-") or "conversa"


def _get_chat_or_404(db: Session, chat_id: int) -> models.Chat:
    chat = db.get(models.Chat, chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat não encontrado")
    return chat


@router.get(
    "",
    response_model=list[schemas.ChatOut],
    summary="List chats",
    response_description="Chats do projeto (ou todos), mais recentes primeiro",
    responses={**UNAUTHORIZED},
)
def list_chats(
    project_id: int | None = Query(
        default=None,
        description="Se informado, filtra chats do projeto",
        examples=[1],
    ),
    db: Session = Depends(get_db),
    _=Depends(require_token),
):
    q = db.query(models.Chat)
    if project_id is not None:
        q = q.filter_by(project_id=project_id)
    return q.order_by(models.Chat.updated_at.desc()).all()


@router.post(
    "",
    response_model=schemas.ChatOut,
    status_code=201,
    summary="Create chat",
    response_description="Chat criado (name vira slug da 1ª mensagem se omitido)",
    responses={**UNAUTHORIZED, **NOT_FOUND, **VALIDATION},
)
def create_chat(
    req: schemas.ChatCreate,
    db: Session = Depends(get_db),
    _=Depends(require_token),
):
    if not db.get(models.Project, req.project_id):
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    chat = models.Chat(
        project_id=req.project_id,
        name=req.name or "new-chat",
        claude_session_id=str(uuid4()),
    )
    db.add(chat)
    db.commit()
    db.refresh(chat)
    return chat


@router.get(
    "/{chat_id}",
    response_model=schemas.ChatOut,
    summary="Get chat",
    response_description="Detalhes do chat",
    responses={**UNAUTHORIZED, **NOT_FOUND},
)
def get_chat(
    chat_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_token),
):
    return _get_chat_or_404(db, chat_id)


@router.delete(
    "/{chat_id}",
    status_code=204,
    summary="Delete chat",
    response_description="Chat e histórico deletados (mensagens em cascata)",
    responses={**UNAUTHORIZED, **NOT_FOUND},
)
def delete_chat(
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
    summary="Rename chat",
    response_description="Chat renomeado",
    responses={**UNAUTHORIZED, **NOT_FOUND, **VALIDATION},
)
def rename_chat(
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
    "/{chat_id}/messages",
    response_model=schemas.MessagePage,
    summary="Chat history (paginated)",
    response_description=(
        "Página de mensagens em ordem cronológica. Sem `cursor` → as "
        "**mais recentes**; com `cursor` → as anteriores àquele id (scroll p/ cima). "
        "`next_cursor: null` = início da conversa."
    ),
    responses={**UNAUTHORIZED, **NOT_FOUND},
)
def list_messages(
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
    q = db.query(models.Message).filter_by(chat_id=chat_id)
    if cursor is not None:
        q = q.filter(models.Message.id < cursor)
    msgs = q.order_by(models.Message.id.desc()).limit(limit).all()
    msgs.reverse()  # ordem cronológica pra exibição
    next_cursor = msgs[0].id if len(msgs) == limit else None
    return schemas.MessagePage(
        messages=[schemas.MessageOut.model_validate(m) for m in msgs],
        next_cursor=next_cursor,
    )


@router.post(
    "/{chat_id}/messages",
    response_model=schemas.MessageOut,
    status_code=201,
    summary="Send message",
    response_description=(
        "Mensagem do usuário gravada, processada pelo Claude Code na sessão do "
        "chat e resposta do assistente gravada e retornada. Payload leve: "
        "**só a última mensagem** — o contexto fica na sessão + no banco."
    ),
    responses={**UNAUTHORIZED, **NOT_FOUND, **VALIDATION, **CLAUDE_ERROR, **CLAUDE_TIMEOUT},
)
def send_message(
    chat_id: int,
    req: schemas.MessageCreate,
    db: Session = Depends(get_db),
    _=Depends(require_token),
):
    chat = _get_chat_or_404(db, chat_id)
    is_first = not db.query(models.Message).filter_by(chat_id=chat.id).first()

    db.add(models.Message(chat_id=chat.id, role="user", content=req.content))
    db.commit()

    try:
        response = run_claude(
            req.content,
            chat.claude_session_id,
            resume=not is_first,
            workdir=chat.project.container_path if chat.project else None,
        )
    except ClaudeTimeout as exc:
        raise HTTPException(status_code=504, detail=str(exc)) from exc
    except ClaudeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    db.add(models.Message(chat_id=chat.id, role="assistant", content=response))
    if chat.name == "new-chat":
        chat.name = slugify(req.content)
    db.commit()

    return db.query(models.Message).order_by(models.Message.id.desc()).first()
