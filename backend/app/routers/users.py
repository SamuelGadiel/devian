from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import AuthContext, hash_password, require_auth
from app.db import get_db

router = APIRouter(prefix="/users", tags=["Users"])

UNAUTHORIZED = {
    401: {
        "description": "Token ausente, inválido ou expirado",
        "model": schemas.ErrorOut,
    }
}
FORBIDDEN = {403: {"description": "Conta inativa ou deletada", "model": schemas.ErrorOut}}
CONFLICT = {409: {"description": "E-mail já usado por outra conta", "model": schemas.ErrorOut}}
VALIDATION = {422: {"description": "Corpo da requisição inválido", "model": schemas.ErrorOut}}


def _current_user(auth: AuthContext) -> models.User:
    """O usuário por trás do access token."""
    return auth.user


@router.get(
    "/me",
    response_model=schemas.UserOut,
    summary="Get current user",
    response_description="Perfil do usuário autenticado",
    responses={**UNAUTHORIZED, **FORBIDDEN},
)
def get_me(auth: AuthContext = Depends(require_auth)):
    return _current_user(auth)


@router.patch(
    "/me",
    response_model=schemas.UserOut,
    summary="Update current user",
    response_description="Atualiza nome, e-mail e/ou foto do usuário autenticado",
    responses={**UNAUTHORIZED, **FORBIDDEN, **CONFLICT, **VALIDATION},
)
def update_me(
    req: schemas.UserUpdate,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(require_auth),
):
    user = _current_user(auth)
    data = req.model_dump(exclude_unset=True)

    if "email" in data and data["email"] and data["email"].lower() != user.email.lower():
        existing = (
            db.query(models.User).filter(models.User.email == data["email"].lower()).first()
        )
        if existing and existing.id != user.id:
            raise HTTPException(status_code=409, detail="E-mail já usado por outra conta")
        user.email = data["email"].lower()
    if "name" in data and data["name"] is not None:
        user.name = data["name"]
    if "picture_url" in data:
        user.picture_url = data["picture_url"]
    if "password" in data and data["password"]:
        user.password_hash = hash_password(data["password"])

    db.commit()
    db.refresh(user)
    return user


@router.delete(
    "/me",
    status_code=204,
    summary="Delete account",
    response_description=(
        "Inativa a conta do usuário (soft delete: status = 'deleted'). "
        "Login futuro com a mesma conta Google retorna 403."
    ),
    responses={**UNAUTHORIZED, **FORBIDDEN},
)
def delete_me(
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(require_auth),
):
    user = _current_user(auth)
    user.status = "deleted"
    db.commit()
