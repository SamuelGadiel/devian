import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import require_token
from app.db import get_db
from app.services.claude import ClaudeError, ClaudeTimeout, run_claude

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=schemas.ChatResponse)
def enviar_mensagem(
    req: schemas.ChatRequest,
    db: Session = Depends(get_db),
    _=Depends(require_token),
):
    """Recebe a mensagem do app, encaminha ao Claude Code (1 chat = 1 sessão)."""
    sessao = db.query(models.Sessao).filter_by(chat_id_app=req.chat_id).first()
    nova = sessao is None
    if nova:
        sessao = models.Sessao(
            chat_id_app=req.chat_id,
            session_id_claude=str(uuid.uuid4()),
            branch=req.branch,
        )
        db.add(sessao)
        db.commit()
        db.refresh(sessao)

    db.add(models.Mensagem(sessao_id=sessao.id, role="user", conteudo=req.mensagem))
    db.commit()

    try:
        resposta = run_claude(req.mensagem, sessao.session_id_claude, resume=not nova)
    except ClaudeTimeout as exc:
        raise HTTPException(status_code=504, detail=str(exc)) from exc
    except ClaudeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    db.add(models.Mensagem(sessao_id=sessao.id, role="assistant", conteudo=resposta))
    db.commit()

    return schemas.ChatResponse(
        chat_id=sessao.chat_id_app,
        session_id=sessao.session_id_claude,
        resposta=resposta,
    )


@router.get("/sessoes", response_model=list[schemas.SessaoOut])
def listar_sessoes(
    db: Session = Depends(get_db),
    _=Depends(require_token),
):
    return db.query(models.Sessao).order_by(models.Sessao.id.desc()).limit(50).all()


@router.get("/sessoes/{sessao_id}", response_model=schemas.SessaoDetalhe)
def detalhe_sessao(
    sessao_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_token),
):
    sessao = db.get(models.Sessao, sessao_id)
    if not sessao:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    return sessao
