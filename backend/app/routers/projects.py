from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import require_token
from app.db import get_db

router = APIRouter(prefix="/projects", tags=["projects"])

UNAUTHORIZED = {401: {"description": "Token Bearer ausente ou inválido"}}
NOT_FOUND = {404: {"description": "Projeto não encontrado"}}
CONFLICT = {409: {"description": "Já existe um projeto com esse nome"}}
VALIDATION = {422: {"description": "Corpo da requisição inválido"}}

AUTH = {"security": [{"HTTPBearer": []}]}


def _get_project_or_404(db: Session, project_id: int) -> models.Project:
    project = db.get(models.Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    return project


@router.get(
    "",
    response_model=list[schemas.ProjectOut],
    summary="List projects",
    response_description="Lista de projetos (ordem alfabética)",
    responses={**UNAUTHORIZED},
)
def list_projects(
    db: Session = Depends(get_db),
    _=Depends(require_token),
):
    return db.query(models.Project).order_by(models.Project.name).all()


@router.post(
    "",
    response_model=schemas.ProjectOut,
    status_code=201,
    summary="Create project",
    response_description="Projeto criado",
    responses={**UNAUTHORIZED, **CONFLICT, **VALIDATION},
)
def create_project(
    req: schemas.ProjectCreate,
    db: Session = Depends(get_db),
    _=Depends(require_token),
):
    existing = db.query(models.Project).filter_by(name=req.name).first()
    if existing:
        raise HTTPException(status_code=409, detail="Projeto já existe")
    project = models.Project(**req.model_dump())
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get(
    "/{project_id}",
    response_model=schemas.ProjectOut,
    summary="Get project",
    response_description="Detalhes do projeto",
    responses={**UNAUTHORIZED, **NOT_FOUND},
)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_token),
):
    return _get_project_or_404(db, project_id)


@router.put(
    "/{project_id}",
    response_model=schemas.ProjectOut,
    summary="Update project",
    response_description="Projeto atualizado (PATCH-like: só os campos enviados)",
    responses={**UNAUTHORIZED, **NOT_FOUND, **CONFLICT, **VALIDATION},
)
def update_project(
    project_id: int,
    req: schemas.ProjectUpdate,
    db: Session = Depends(get_db),
    _=Depends(require_token),
):
    project = _get_project_or_404(db, project_id)
    data = req.model_dump(exclude_unset=True)
    if "name" in data and data["name"] != project.name:
        existing = (
            db.query(models.Project)
            .filter(
                models.Project.name == data["name"],
                models.Project.id != project_id,
            )
            .first()
        )
        if existing:
            raise HTTPException(status_code=409, detail="Projeto já existe")
    for field, value in data.items():
        setattr(project, field, value)
    db.commit()
    db.refresh(project)
    return project


@router.delete(
    "/{project_id}",
    status_code=204,
    summary="Delete project",
    response_description="Projeto deletado (cascata: chats, mensagens e artefatos)",
    responses={**UNAUTHORIZED, **NOT_FOUND},
)
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_token),
):
    project = _get_project_or_404(db, project_id)
    db.delete(project)
    db.commit()
