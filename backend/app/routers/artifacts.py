from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import require_token
from app.config import settings
from app.db import get_db

router = APIRouter(prefix="/projects/{project_id}/artifacts", tags=["artifacts"])

UNAUTHORIZED = {401: {"description": "Token Bearer ausente ou inválido"}}
NOT_FOUND = {404: {"description": "Projeto, artefato ou arquivo não encontrado"}}


def _artifacts_dir(project_id: int) -> Path:
    d = Path(settings.storage_dir) / "artifacts" / str(project_id)
    d.mkdir(parents=True, exist_ok=True)
    return d


@router.get(
    "",
    response_model=list[schemas.ArtifactOut],
    summary="List project artifacts",
    response_description="Artefatos (APKs, relatórios…) mais recentes primeiro",
    responses={**UNAUTHORIZED, **NOT_FOUND},
)
def list_artifacts(
    project_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_token),
):
    if not db.get(models.Project, project_id):
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    return (
        db.query(models.Artifact)
        .filter_by(project_id=project_id)
        .order_by(models.Artifact.id.desc())
        .all()
    )


@router.get(
    "/{artifact_id}",
    summary="Download artifact",
    response_description=(
        "Stream do arquivo (APK) para instalação no celular. "
        "Header `Content-Disposition: attachment` com o nome do arquivo."
    ),
    responses={**UNAUTHORIZED, **NOT_FOUND},
)
def download_artifact(
    project_id: int,
    artifact_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_token),
):
    artifact = (
        db.query(models.Artifact)
        .filter_by(id=artifact_id, project_id=project_id)
        .first()
    )
    if not artifact:
        raise HTTPException(status_code=404, detail="Artefato não encontrado")
    path = _artifacts_dir(project_id) / artifact.filename
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Arquivo não encontrado no storage")
    return FileResponse(
        path,
        filename=artifact.filename,
        media_type=artifact.content_type or "application/octet-stream",
    )
