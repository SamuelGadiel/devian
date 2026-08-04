import re
import unicodedata
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import require_token
from app.db import get_db
from app.services.claude import ClaudeError, ClaudeTimeout, run_claude

router = APIRouter(prefix="/chats", tags=["chats"])


def _slugify(texto: str, max_len: int = 50) -> str:
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


@router.get("", response_model=list[schemas.ChatOut])
def listar_chats(
    projeto_id: int | None = Query(default=None, description="Filtra por projeto"),
    db: Session = Depends(get_db),
    _=Depends(require_token),
):
    """Lista chats (opcionalmente de um projeto), mais recentes primeiro."""
    q = db.query(models.Chat)
    if projeto_id is not None:
        q = q.filter_by(projeto_id=projeto_id)
    return q.order_by(models.Chat.atualizada_em.desc()).all()


@router.post("", response_model=schemas.ChatOut, status_code=201)
def criar_chat(
    req: schemas.ChatCreate,
    db: Session = Depends(get_db),
    _=Depends(require_token),
):
    """Cria um chat novo no projeto. O name vira slug da 1ª mensagem se não vier."""
    if not db.get(models.Projeto, req.projeto_id):
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    chat = models.Chat(
        projeto_id=req.projeto_id,
        name=req.name or "novo-chat",
        session_id_claude=str(uuid.uuid4()),
    )
    db.add(chat)
    db.commit()
    db.refresh(chat)
    return chat


@router.get("/{chat_id}", response_model=schemas.ChatOut)
def obter_chat(
    chat_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_token),
):
    return _get_chat_or_404(db, chat_id)


@router.delete("/{chat_id}", status_code=204)
def deletar_chat(
    chat_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_token),
):
    """Deleta o chat e todo o histórico (mensagens em cascata)."""
    chat = _get_chat_or_404(db, chat_id)
    db.delete(chat)
    db.commit()


@router.put("/{chat_id}/rename", response_model=schemas.ChatOut)
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


@router.get("/{chat_id}/mensagens", response_model=schemas.MensagemPage)
def listar_mensagens(
    chat_id: int,
    cursor: int | None = Query(default=None, description="Id da msg mais antiga da página atual"),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    _=Depends(require_token),
):
    """Histórico paginado (cursor-based).

    Sem cursor: retorna as MAIS RECENTES (últimas N). Com cursor: retorna as N
    anteriores à mensagem de cursor (scroll para cima). Resposta em ordem
    cronológica (antiga -> nova), pronta pra exibir.
    """
    _get_chat_or_404(db, chat_id)
    q = db.query(models.Mensagem).filter_by(chat_id=chat_id)
    if cursor is not None:
        q = q.filter(models.Mensagem.id < cursor)
    msgs = q.order_by(models.Mensagem.id.desc()).limit(limit).all()
    msgs.reverse()  # ordem cronológica pra exibição
    next_cursor = msgs[0].id if len(msgs) == limit else None
    return schemas.MensagemPage(mensagens=msgs, next_cursor=next_cursor)


@router.post("/{chat_id}/mensagens", response_model=schemas.MensagemOut, status_code=201)
def enviar_mensagem(
    chat_id: int,
    req: schemas.MensagemCreate,
    db: Session = Depends(get_db),
    _=Depends(require_token),
):
    """Envia mensagem. O app manda SÓ a última mensagem — o contexto da sessão
    fica no Claude Code (--resume) e o histórico no banco. Payload leve sempre."""
    chat = _get_chat_or_404(db, chat_id)
    primeira = (
        db.query(func.count(models.Mensagem.id)).filter_by(chat_id=chat.id).scalar() == 0
    )

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
        chat.name = _slugify(req.conteudo)
    db.commit()

    return db.query(models.Mensagem).order_by(models.Mensagem.id.desc()).first()
