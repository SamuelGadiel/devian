from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import require_token
from app.db import get_db

router = APIRouter(prefix="/projetos", tags=["projetos"])


@router.get("", response_model=list[schemas.ProjetoOut])
def listar_projetos(
    db: Session = Depends(get_db),
    _=Depends(require_token),
):
    return db.query(models.Projeto).order_by(models.Projeto.nome).all()


@router.post("", response_model=schemas.ProjetoOut)
def criar_projeto(
    req: schemas.ProjetoCreate,
    db: Session = Depends(get_db),
    _=Depends(require_token),
):
    existente = db.query(models.Projeto).filter_by(nome=req.nome).first()
    if existente:
        raise HTTPException(status_code=409, detail="Projeto já existe")
    projeto = models.Projeto(
        nome=req.nome, repo_url=req.repo_url, branch_padrao=req.branch_padrao
    )
    db.add(projeto)
    db.commit()
    db.refresh(projeto)
    return projeto
