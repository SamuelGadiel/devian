from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import require_token
from app.config import settings
from app.db import get_db

router = APIRouter(prefix="/projetos/{projeto_id}/artefatos", tags=["artefatos"])

UNAUTHORIZED = {401: {"description": "Token Bearer ausente ou inválido"}}
NOT_FOUND = {404: {"description": "Projeto, artefato ou arquivo não encontrado"}}


def _dir_artefatos(projeto_id: int) -> Path:
    d = Path(settings.storage_dir) / "artefatos" / str(projeto_id)
    d.mkdir(parents=True, exist_ok=True)
    return d


@router.get(
    "",
    response_model=list[schemas.ArtefatoOut],
    summary="Listar artefatos do projeto",
    response_description="Artefatos (APKs, relatórios…) mais recentes primeiro",
    responses={**UNAUTHORIZED, **NOT_FOUND},
)
def listar_artefatos(
    projeto_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_token),
):
    if not db.get(models.Projeto, projeto_id):
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    return (
        db.query(models.Artefato)
        .filter_by(projeto_id=projeto_id)
        .order_by(models.Artefato.id.desc())
        .all()
    )


@router.get(
    "/{artefato_id}",
    summary="Baixar artefato",
    response_description=(
        "Stream do arquivo (APK) para instalação no celular. "
        "Header `Content-Disposition: attachment` com o nome do arquivo."
    ),
    responses={**UNAUTHORIZED, **NOT_FOUND},
)
def baixar_artefato(
    projeto_id: int,
    artefato_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_token),
):
    artefato = (
        db.query(models.Artefato)
        .filter_by(id=artefato_id, projeto_id=projeto_id)
        .first()
    )
    if not artefato:
        raise HTTPException(status_code=404, detail="Artefato não encontrado")
    caminho = _dir_artefatos(projeto_id) / artefato.nome_arquivo
    if not caminho.is_file():
        raise HTTPException(status_code=404, detail="Arquivo não encontrado no storage")
    return FileResponse(
        caminho,
        filename=artefato.nome_arquivo,
        media_type=artefato.content_type or "application/octet-stream",
    )
