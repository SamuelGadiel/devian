from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import AuthContext, require_auth
from app.db import get_db
from app.services.claude import ClaudeError, ClaudeTimeout, resolve_workdir, run_claude
from app.slug import slugify

router = APIRouter(
    prefix="/projects/{project_id}/chats/{chat_id}/messages", tags=["Messages"]
)

UNAUTHORIZED = {401: {"description": "Token Bearer ausente ou inválido", "model": schemas.ErrorOut}}
NOT_FOUND = {404: {"description": "Projeto ou chat não encontrado", "model": schemas.ErrorOut}}
VALIDATION = {422: {"description": "Corpo da requisição inválido", "model": schemas.ErrorOut}}
CLAUDE_ERROR = {502: {"description": "Erro do Claude Code no container (ClaudeError)", "model": schemas.ErrorOut}}
CLAUDE_TIMEOUT = {504: {"description": "O Claude Code não respondeu a tempo (timeout)", "model": schemas.ErrorOut}}


def _get_chat_in_project_or_404(
    db: Session, project_id: UUID, chat_id: UUID, user_id: UUID | None = None
) -> models.Chat:
    q = (
        db.query(models.Chat)
        .join(models.Project)
        .filter(models.Chat.id == chat_id, models.Chat.project_id == project_id)
    )
    if user_id is not None:
        q = q.filter(models.Project.user_id == user_id)
    chat = q.first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat não encontrado")
    return chat


@router.get(
    "",
    response_model=schemas.MessagePage,
    summary="Chat history (paginated)",
    response_description=(
        "Página de mensagens em ordem cronológica. Sem `cursor` → as "
        "**mais recentes**; com `cursor` (UUID da msg mais antiga da página) → "
        "as anteriores (scroll p/ cima). `next_cursor: null` = início da conversa."
    ),
    responses={**UNAUTHORIZED, **NOT_FOUND},
)
def list_messages(
    project_id: UUID,
    chat_id: UUID,
    cursor: UUID | None = Query(
        default=None,
        description=(
            "UUID da mensagem mais antiga da página atual. Passe o `next_cursor` "
            "retornado para buscar as anteriores."
        ),
        examples=["0191f3b2-4c3a-7b00-8000-000000000013"],
    ),
    limit: int = Query(
        default=50,
        ge=1,
        le=200,
        description="Quantidade de mensagens por página (1–200)",
        examples=[50],
    ),
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(require_auth),
):
    _get_chat_in_project_or_404(db, project_id, chat_id, auth.user_id)
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
    "",
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
    project_id: UUID,
    chat_id: UUID,
    req: schemas.MessageCreate,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(require_auth),
):
    chat = _get_chat_in_project_or_404(db, project_id, chat_id, auth.user_id)
    is_first = not db.query(models.Message).filter_by(chat_id=chat.id).first()

    db.add(models.Message(chat_id=chat.id, role="user", content=req.content))
    db.commit()

    try:
        response = run_claude(
            req.content,
            chat.claude_session_id,
            resume=not is_first,
            workdir=resolve_workdir(chat.project) if chat.project else None,
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
