"""Teste do fluxo de auth e-mail+senha (v0.7.0) contra um banco efêmero.

Roda com TestClient contra um Postgres isolado. Cria os usuários de teste
direto no banco (não existe endpoint de registro — o cadastro é seed).

Uso:
    DEVIAN_DATABASE_URL=postgresql+psycopg2://postgres:test@127.0.0.1:5544/devian_test \
    PYTHONPATH=. .venv/bin/python tests/test_auth_flow.py
"""
import os

os.environ["DEVIAN_SESSION_JWT_SECRET"] = "a" * 64
os.environ["DEVIAN_ACCESS_TOKEN_TTL_MINUTES"] = "60"
os.environ["DEVIAN_REFRESH_TOKEN_TTL_DAYS"] = "90"

from fastapi.testclient import TestClient  # noqa: E402

from app import models  # noqa: E402
from app.auth import hash_password  # noqa: E402
from app.db import SessionLocal  # noqa: E402
from app.main import app  # noqa: E402

client = TestClient(app)

PASS = 0


def check(label: str, cond: bool, extra: str = ""):
    global PASS
    status = "PASS" if cond else "FAIL"
    print(f"[{status}] {label}" + (f" — {extra}" if extra else ""))
    if not cond:
        raise SystemExit(f"FALHOU em: {label}")


def seed_user(email: str, password: str, name: str = "Tester", role: str = "member") -> models.User:
    db = SessionLocal()
    try:
        user = db.query(models.User).filter_by(email=email).first()
        if user is None:
            user = models.User(
                email=email,
                name=name,
                password_hash=hash_password(password),
                role=role,
                status="active",
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        return user
    finally:
        db.close()


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# Setup: admin + member
admin = seed_user("admin@devian.app", "senha-admin-1", "Admin", "admin")
member = seed_user("member@devian.app", "senha-member-1", "Member", "member")

# 1. Health público
r = client.get("/devian/health")
check("health público", r.status_code == 200 and r.json()["status"] == "ok", str(r.status_code))

# 2. Login correto → access + refresh + user
r = client.post("/devian/auth/login", json={"email": "admin@devian.app", "password": "senha-admin-1"})
check("login ok → 200", r.status_code == 200, r.text[:100])
body = r.json()
access = body["access_token"]
refresh = body["refresh_token"]
check("login sem token_type", "token_type" not in body)
check("login sem role/status expostos", "role" not in body["user"] and "status" not in body["user"])
check("login devolve user admin", body["user"]["email"] == "admin@devian.app")

# 3. Senha errada → 401 (mesma msg p/ e-mail inexistente)
r = client.post("/devian/auth/login", json={"email": "admin@devian.app", "password": "errada"})
check("senha errada → 401", r.status_code == 401 and "inválidos" in r.json()["message"])
r = client.post("/devian/auth/login", json={"email": "naoexiste@devian.app", "password": "qualquer"})
check("e-mail inexistente → 401", r.status_code == 401)

# 4. /users/me com access token
r = client.get("/devian/users/me", headers=auth(access))
check("GET /users/me → 200", r.status_code == 200 and r.json()["email"] == "admin@devian.app")

# 5. Access inválido → 401
r = client.get("/devian/users/me", headers=auth("not-a-jwt"))
check("access inválido → 401", r.status_code == 401)

# 6. Token de máquina MORTO — qualquer string antiga não autentica mais
r = client.get("/devian/projects", headers=auth("machine-token-test"))
check("token de máquina morto → 401", r.status_code == 401)

# 7. Criar projeto com access → user_id = admin
r = client.post(
    "/devian/projects",
    json={"name": "projeto-admin", "repo_url": "git@github.com:x/y.git"},
    headers=auth(access),
)
check("criar projeto → 201", r.status_code == 201, r.text[:100])
proj_id = r.json()["id"]
check("projeto tem user_id = admin", r.json()["user_id"] == str(admin.id))

# 8. Adoção de órfãos: projeto sem user_id (criado por seed direto) → login do admin adota
db = SessionLocal()
try:
    orphan = models.Project(name="projeto-orphan", user_id=None, branch="main")
    db.add(orphan)
    db.commit()
    orphan_id = str(orphan.id)
finally:
    db.close()
r = client.post("/devian/auth/login", json={"email": "admin@devian.app", "password": "senha-admin-1"})
access = r.json()["access_token"]
r = client.get(f"/devian/projects/{orphan_id}", headers=auth(access))
check("órfão adotado no login do admin", r.status_code == 200 and r.json()["user_id"] == str(admin.id), r.text[:80])

# 9. Scoping: member não vê projetos do admin
r = client.post("/devian/auth/login", json={"email": "member@devian.app", "password": "senha-member-1"})
member_access = r.json()["access_token"]
r = client.get("/devian/projects", headers=auth(member_access))
check("member não vê projetos do admin", r.json() == [], str(r.json()))
r = client.get(f"/devian/projects/{proj_id}", headers=auth(member_access))
check("member não acessa projeto do admin → 404", r.status_code == 404)

# 10. Refresh rotaciona: par novo, token antigo morre
r = client.post("/devian/auth/refresh", json={"refresh_token": refresh})
check("refresh → 200", r.status_code == 200, r.text[:100])
new_refresh = r.json()["refresh_token"]
check("refresh devolve access novo", bool(r.json()["access_token"]))
r = client.post("/devian/auth/refresh", json={"refresh_token": refresh})
check("refresh token antigo revogado → 401", r.status_code == 401)

# 11. Logout revoga; idempotente
r = client.post("/devian/auth/logout", json={"refresh_token": new_refresh})
check("logout → 204", r.status_code == 204)
r = client.post("/devian/auth/refresh", json={"refresh_token": new_refresh})
check("refresh após logout → 401", r.status_code == 401)
r = client.post("/devian/auth/logout", json={"refresh_token": new_refresh})
check("logout idempotente → 204", r.status_code == 204)

# 12. PATCH /users/me troca senha → login com nova ok, antiga 401
r = client.patch("/devian/users/me", json={"password": "senha-nova-2"}, headers=auth(access))
check("PATCH senha → 200", r.status_code == 200)
r = client.post("/devian/auth/login", json={"email": "admin@devian.app", "password": "senha-admin-1"})
check("senha antiga → 401", r.status_code == 401)
r = client.post("/devian/auth/login", json={"email": "admin@devian.app", "password": "senha-nova-2"})
check("senha nova → 200", r.status_code == 200)

# 13. Usuário inativo → 403 no login
db = SessionLocal()
try:
    blocked = db.query(models.User).filter_by(email="member@devian.app").first()
    assert blocked is not None
    blocked.status = "deleted"
    db.commit()
finally:
    db.close()
r = client.post("/devian/auth/login", json={"email": "member@devian.app", "password": "senha-member-1"})
check("usuário inativo → 403", r.status_code == 403)

print("\nTODOS OS TESTES PASSARAM")
