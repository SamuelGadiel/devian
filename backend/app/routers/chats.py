import re
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import AuthContext, require_auth
from app.db import get_db
from app.slug import slugify

router = APIRouter(prefix="/projects/{project_id}/chats", tags=["Chats"])

UNAUTHORIZED = {401: {"description": "Token Bearer ausente ou inválido", "model": schemas.ErrorOut}}
NOT_FOUND = {404: {"description": "Projeto ou chat não encontrado", "model": schemas.ErrorOut}}
VALIDATION = {422: {"description": "Corpo da requisição inválido", "model": schemas.ErrorOut}}


def _get_project_or_404(
    db: Session, project_id: UUID, user_id: UUID | None = None
) -> models.Project:
    q = db.query(models.Project).filter(models.Project.id == project_id)
    if user_id is not None:
        q = q.filter(models.Project.user_id == user_id)
    project = q.first()
    if not project:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    return project


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
    response_model=list[schemas.ChatOut],
    summary="List chats",
    response_description="Chats do projeto, mais recentes primeiro",
    responses={**UNAUTHORIZED, **NOT_FOUND},
)
def list_chats(
    project_id: UUID,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(require_auth),
):
    _get_project_or_404(db, project_id, auth.user_id)
    return (
        db.query(models.Chat)
        .filter_by(project_id=project_id)
        .order_by(models.Chat.updated_at.desc())
        .all()
    )


@router.post(
    "",
    response_model=schemas.ChatOut,
    status_code=201,
    summary="Create chat",
    response_description=(
        "Chat criado. Herda a `branch` do projeto; `name` vira slug da 1ª "
        "mensagem se omitido."
    ),
    responses={**UNAUTHORIZED, **NOT_FOUND, **VALIDATION},
)
def create_chat(
    project_id: UUID,
    req: schemas.ChatCreate,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(require_auth),
):
    project = _get_project_or_404(db, project_id, auth.user_id)
    chat = models.Chat(
        project_id=project_id,
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
    project_id: UUID,
    chat_id: UUID,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(require_auth),
):
    return _get_chat_in_project_or_404(db, project_id, chat_id, auth.user_id)


@router.delete(
    "/{chat_id}",
    status_code=204,
    summary="Delete chat",
    response_description="Chat e histórico deletados (mensagens em cascata)",
    responses={**UNAUTHORIZED, **NOT_FOUND},
)
def delete_chat(
    project_id: UUID,
    chat_id: UUID,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(require_auth),
):
    chat = _get_chat_in_project_or_404(db, project_id, chat_id, auth.user_id)
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
    project_id: UUID,
    chat_id: UUID,
    req: schemas.ChatRename,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(require_auth),
):
    chat = _get_chat_in_project_or_404(db, project_id, chat_id, auth.user_id)
    chat.name = req.name
    db.commit()
    db.refresh(chat)
    return chat
