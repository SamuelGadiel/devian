"""Teste do fluxo de auth (v0.6.0) contra um banco efêmero.

Roda com TestClient + monkeypatch do verify_google_id_token (sem depender
do Google real). Usa DEVIAN_DATABASE_URL apontando pro banco de teste.

Uso:
    DEVIAN_DATABASE_URL=postgresql+psycopg2://postgres:test@127.0.0.1:5544/devian_test \
    .venv/bin/python tests/test_auth_flow.py
"""
import os

os.environ["DEVIAN_GOOGLE_CLIENT_ID"] = "test-client-id"
os.environ["DEVIAN_SESSION_JWT_SECRET"] = "a" * 64
os.environ["DEVIAN_ALLOWED_LOGIN_EMAILS"] = "samuel@agapech.com.br,outro@exemplo.com"
os.environ["DEVIAN_API_TOKEN"] = "machine-token-test"

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from app.routers import auth as auth_router  # noqa: E402  (função importada direto)

client = TestClient(app)

PASS = 0


def check(label: str, cond: bool, extra: str = ""):
    global PASS
    status = "PASS" if cond else "FAIL"
    print(f"[{status}] {label}" + (f" — {extra}" if extra else ""))
    if not cond:
        raise SystemExit(f"FALHOU em: {label}")


def fake_info(sub: str, email: str, name: str = "Tester"):
    return {
        "iss": "accounts.google.com",
        "aud": "test-client-id",
        "sub": sub,
        "email": email,
        "email_verified": True,
        "name": name,
        "picture": f"https://pic/{sub}.jpg",
    }


# 1. Health público
r = client.get("/devian/health")
check("health público", r.status_code == 200 and r.json()["status"] == "ok", str(r.status_code))

# 2. Login sem token do Google válido → 401
r = client.post("/devian/auth/login", json={"id_token": "garbage"})
check("login com token inválido → 401", r.status_code == 401, r.text[:80])

# 3. Login real (primeiro usuário → admin) — monkeypatch da validação
auth_router.verify_google_id_token = lambda token, cid: fake_info("sub-samuel", "samuel@agapech.com.br", "Samuel")
r = client.post("/devian/auth/login", json={"id_token": "fake-google-token"})
check("login 1º usuário → 200", r.status_code == 200, r.text[:120])
body = r.json()
token_samuel = body["token"]
check("login devolve token + user", bool(token_samuel) and body["user"]["role"] == "admin", body["user"]["role"])
samuel_id = body["user"]["id"]
check("user tem foto/nome", body["user"]["name"] == "Samuel" and body["user"]["picture_url"] == "https://pic/sub-samuel.jpg")

# 4. /users/me com o JWT
r = client.get("/devian/users/me", headers={"Authorization": f"Bearer {token_samuel}"})
check("GET /users/me → 200", r.status_code == 200 and r.json()["email"] == "samuel@agapech.com.br", r.text[:80])

# 5. /users/me com token inválido → 401
r = client.get("/devian/users/me", headers={"Authorization": "Bearer not-a-jwt"})
check("GET /users/me token inválido → 401", r.status_code == 401)

# 6. Criação de projeto com JWT (fica do Samuel)
r = client.post(
    "/devian/projects",
    json={"name": "projeto-do-samuel", "repo_url": "git@github.com:x/y.git"},
    headers={"Authorization": f"Bearer {token_samuel}"},
)
check("criar projeto do samuel → 201", r.status_code == 201, r.text[:120])
proj_id = r.json()["id"]
check("projeto tem user_id = samuel", r.json()["user_id"] == samuel_id)

# 7. Projeto órfão criado por token de máquina → adotado no login do admin
r = client.post(
    "/devian/projects",
    json={"name": "projeto-maquina", "repo_url": "git@github.com:x/machine.git"},
    headers={"Authorization": "Bearer machine-token-test"},
)
check("criar projeto via máquina → 201", r.status_code == 201)
maq_id = r.json()["id"]
r = client.post("/devian/auth/login", json={"id_token": "fake-google-token"})
token_samuel = r.json()["token"]
r = client.get("/devian/projects", headers={"Authorization": f"Bearer {token_samuel}"})
ids = [p["id"] for p in r.json()]
check("admin vê projeto da máquina (adotado)", maq_id in ids, str(ids))
r = client.get(f"/devian/projects/{maq_id}", headers={"Authorization": f"Bearer {token_samuel}"})
check("projeto adotado tem user_id = samuel", r.json()["user_id"] == samuel_id)

# 8. Segundo usuário (allowlist) → member, não vê nada do Samuel
auth_router.verify_google_id_token = lambda token, cid: fake_info("sub-outro", "outro@exemplo.com", "Outro")
r = client.post("/devian/auth/login", json={"id_token": "fake-google-token"})
check("login 2º usuário → 200", r.status_code == 200, r.text[:120])
token_outro = r.json()["token"]
check("2º usuário é member", r.json()["user"]["role"] == "member")
r = client.get("/devian/projects", headers={"Authorization": f"Bearer {token_outro}"})
check("member não vê projetos do admin", r.json() == [], str(r.json()))
r = client.get(f"/devian/projects/{proj_id}", headers={"Authorization": f"Bearer {token_outro}"})
check("member não acessa projeto do admin → 404", r.status_code == 404)

# 9. Usuário fora do allowlist → 403 (nem é criado)
auth_router.verify_google_id_token = lambda token, cid: fake_info("sub-intruso", "intruso@exemplo.com")
r = client.post("/devian/auth/login", json={"id_token": "fake-google-token"})
check("login fora do allowlist → 403", r.status_code == 403, r.text[:80])

# 10. Update de perfil (PATCH /users/me)
r = client.patch(
    "/devian/users/me",
    json={"name": "Samuel G.", "picture_url": "https://nova-foto.jpg"},
    headers={"Authorization": f"Bearer {token_samuel}"},
)
check("PATCH /users/me → 200", r.status_code == 200 and r.json()["name"] == "Samuel G.", r.text[:120])
check("PATCH atualiza foto", r.json()["picture_url"] == "https://nova-foto.jpg")

# 11. Delete conta (soft delete) → 204; login seguinte → 403
r = client.delete("/devian/users/me", headers={"Authorization": f"Bearer {token_outro}"})
check("DELETE /users/me → 204", r.status_code == 204)
r = client.post("/devian/auth/login", json={"id_token": "fake-google-token"})
check("login após deletar → 403", r.status_code == 403, r.text[:80])

# 12. Regressão: token de máquina continua vendo tudo (age como admin)
r = client.get("/devian/projects", headers={"Authorization": "Bearer machine-token-test"})
check("máquina vê projetos", len(r.json()) == 2, str(len(r.json())))

print("\nTODOS OS TESTES PASSARAM")
