#!/usr/bin/env python3
"""Cria/atualiza um usuário com e-mail e senha (seed administrativo).

Uso (a senha NUNCA vai para o repositório — vem do ambiente):
    SEED_EMAIL=... SEED_NAME=... SEED_PASSWORD=... .venv/bin/python scripts/seed_user.py

O usuário seedado nasce (ou vira) admin + active.
"""
import os

from app import models
from app.auth import hash_password
from app.db import SessionLocal


def main() -> None:
    email = os.environ["SEED_EMAIL"].strip().lower()
    name = os.environ["SEED_NAME"].strip()
    password = os.environ["SEED_PASSWORD"]

    db = SessionLocal()
    try:
        user = db.query(models.User).filter_by(email=email).first()
        if user is None:
            user = models.User(
                email=email,
                name=name,
                password_hash=hash_password(password),
                role="admin",
                status="active",
            )
            db.add(user)
            print(f"Usuário criado: {email} (admin)")
        else:
            user.name = name
            user.password_hash = hash_password(password)
            user.role = "admin"
            user.status = "active"
            print(f"Usuário atualizado: {email} (admin, senha nova)")
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    main()
