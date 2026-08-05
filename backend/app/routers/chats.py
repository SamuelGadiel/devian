import re
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import require_token
from app.db import get_db
from app.slug import slugify

router = APIRouter(prefix="/projects/{project_id}/chats", tags=["Chats"])

UNAUTHORIZED = {401: {"description": "Token Bearer ausente ou inválido", "model": schemas.ErrorOut}}
NOT_FOUND = {404: {"description": "Projeto ou chat não encontrado", "model": schemas.ErrorOut}}
VALIDATION = {422: {"description": "Corpo da requisição inválido", "model": schemas.ErrorOut}}


def _get_project_or_404(db: Session, project_id: UUID) -> models.Project:
    project = db.get(models.Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    return project


def _get_chat_in_project_or_404(
    db: Session, project_id: UUID, chat_id: UUID
) -> models.Chat:
    chat = db.get(models.Chat, chat_id)
    if not chat or chat.project_id != project_id:
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
    _=Depends(require_token),
):
    _get_project_or_404(db, project_id)
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
    _=Depends(require_token),
):
    project = _get_project_or_404(db, project_id)
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
    _=Depends(require_token),
):
    return _get_chat_in_project_or_404(db, project_id, chat_id)


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
    _=Depends(require_token),
):
    chat = _get_chat_in_project_or_404(db, project_id, chat_id)
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
    _=Depends(require_token),
):
    chat = _get_chat_in_project_or_404(db, project_id, chat_id)
    chat.name = req.name
    db.commit()
    db.refresh(chat)
    return chat
