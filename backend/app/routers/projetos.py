from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import require_token
from app.db import get_db

router = APIRouter(prefix="/projetos", tags=["projetos"])

UNAUTHORIZED = {401: {"description": "Token Bearer ausente ou inválido"}}
NOT_FOUND = {404: {"description": "Projeto não encontrado"}}
CONFLICT = {409: {"description": "Já existe um projeto com esse nome"}}
VALIDATION = {422: {"description": "Corpo da requisição inválido"}}

AUTH = {"security": [{"HTTPBearer": []}]}


def _get_projeto_or_404(db: Session, projeto_id: int) -> models.Projeto:
    projeto = db.get(models.Projeto, projeto_id)
    if not projeto:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    return projeto


@router.get(
    "",
    response_model=list[schemas.ProjetoOut],
    summary="Listar projetos",
    response_description="Lista de projetos (ordem alfabética)",
    responses={**UNAUTHORIZED},
)
def listar_projetos(
    db: Session = Depends(get_db),
    _=Depends(require_token),
):
    return db.query(models.Projeto).order_by(models.Projeto.nome).all()


@router.post(
    "",
    response_model=schemas.ProjetoOut,
    status_code=201,
    summary="Criar projeto",
    response_description="Projeto criado",
    responses={**UNAUTHORIZED, **CONFLICT, **VALIDATION},
)
def criar_projeto(
    req: schemas.ProjetoCreate,
    db: Session = Depends(get_db),
    _=Depends(require_token),
):
    existente = db.query(models.Projeto).filter_by(nome=req.nome).first()
    if existente:
        raise HTTPException(status_code=409, detail="Projeto já existe")
    projeto = models.Projeto(**req.model_dump())
    db.add(projeto)
    db.commit()
    db.refresh(projeto)
    return projeto


@router.get(
    "/{projeto_id}",
    response_model=schemas.ProjetoOut,
    summary="Obter projeto",
    response_description="Detalhes do projeto",
    responses={**UNAUTHORIZED, **NOT_FOUND},
)
def obter_projeto(
    projeto_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_token),
):
    return _get_projeto_or_404(db, projeto_id)


@router.put(
    "/{projeto_id}",
    response_model=schemas.ProjetoOut,
    summary="Atualizar projeto",
    response_description="Projeto atualizado (PATCH-like: só os campos enviados)",
    responses={**UNAUTHORIZED, **NOT_FOUND, **CONFLICT, **VALIDATION},
)
def atualizar_projeto(
    projeto_id: int,
    req: schemas.ProjetoUpdate,
    db: Session = Depends(get_db),
    _=Depends(require_token),
):
    projeto = _get_projeto_or_404(db, projeto_id)
    dados = req.model_dump(exclude_unset=True)
    if "nome" in dados and dados["nome"] != projeto.nome:
        existente = (
            db.query(models.Projeto)
            .filter(
                models.Projeto.nome == dados["nome"],
                models.Projeto.id != projeto_id,
            )
            .first()
        )
        if existente:
            raise HTTPException(status_code=409, detail="Projeto já existe")
    for campo, valor in dados.items():
        setattr(projeto, campo, valor)
    db.commit()
    db.refresh(projeto)
    return projeto


@router.delete(
    "/{projeto_id}",
    status_code=204,
    summary="Deletar projeto",
    response_description="Projeto deletado (cascata: chats, mensagens e artefatos)",
    responses={**UNAUTHORIZED, **NOT_FOUND},
)
def deletar_projeto(
    projeto_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_token),
):
    projeto = _get_projeto_or_404(db, projeto_id)
    db.delete(projeto)
    db.commit()
