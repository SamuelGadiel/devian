from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.timezones import BrDateTime

# ============================================================
# Erro padrão — TODOS os erros respondem {"message": "..."}
# ============================================================


class ErrorOut(BaseModel):
    """Resposta de erro padrão da API."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "message": "Projeto não encontrado",
                }
            ]
        }
    )

    message: str = Field(description="Mensagem de erro (em português)")

# ============================================================
# Projects
# ============================================================


class ProjectCreate(BaseModel):
    """Creates a project from an EXISTING repository."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "name": "sisvisa",
                    "repo_url": "git@bitbucket.org:branef/sisvisa-serr-mobile.git",
                    "branch": "develop",
                }
            ]
        }
    )

    name: str = Field(
        min_length=1,
        max_length=100,
        description="Short project name. Becomes the unique identifier.",
        examples=["sisvisa"],
    )
    repo_url: str | None = Field(
        default=None,
        description="URL of the existing repository (git@ or https://).",
        examples=["git@bitbucket.org:branef/sisvisa-serr-mobile.git"],
    )
    branch: str = Field(
        default="main",
        description="Branch the project works on (used by builds and new chats).",
        examples=["develop"],
    )


class ProjectUpdate(BaseModel):
    """Partial update — send only the fields you want to change."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "branch": "develop",
                }
            ]
        }
    )

    name: str | None = Field(default=None, min_length=1, max_length=100)
    repo_url: str | None = None
    branch: str | None = None


class ProjectOut(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": "0191f3b2-4c3a-7b00-8000-000000000001",
                    "name": "sisvisa",
                    "repo_url": "git@bitbucket.org:branef/sisvisa-serr-mobile.git",
                    "branch": "develop",
                    "created_at": "2026-08-05T16:00:00Z",
                    "updated_at": "2026-08-05T16:00:00Z",
                }
            ]
        },
    )

    id: UUID
    user_id: UUID | None = Field(
        default=None,
        description="Owner user id. Null for projects created by machine token before the first login (adopted by the admin on login).",
    )
    name: str
    repo_url: str | None
    branch: str
    created_at: BrDateTime
    updated_at: BrDateTime


# ============================================================
# Chats (aninhados em /projects/{project_id}/chats)
# ============================================================


class ChatCreate(BaseModel):
    """Opens a new chat inside a project (project comes from the URL)."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "name": "nova-feature",
                }
            ]
        }
    )

    name: str | None = Field(
        default=None,
        max_length=100,
        description=(
            "Chat name/slug. If omitted, it starts as 'new-chat' and becomes "
            "the slug of the first message (e.g. 'qual-a-cor')."
        ),
        examples=["nova-feature"],
    )


class ChatRename(BaseModel):
    """Renames the slug shown in the drawer."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "name": "ajuste-no-relatorio",
                }
            ]
        }
    )

    name: str = Field(min_length=1, max_length=100)


class ChatOut(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": "0191f3b2-4c3a-7b00-8000-00000000000a",
                    "project_id": "0191f3b2-4c3a-7b00-8000-000000000001",
                    "name": "qual-a-cor",
                    "created_at": "2026-08-05T16:00:00Z",
                    "updated_at": "2026-08-05T16:00:05Z",
                }
            ]
        },
    )

    id: UUID
    project_id: UUID
    name: str
    created_at: BrDateTime
    updated_at: BrDateTime


# ============================================================
# Messages (aninhadas em /projects/{project_id}/chats/{chat_id}/messages)
# ============================================================


class MessageCreate(BaseModel):
    """The user's next message. That's it — no history in the payload."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "content": "Pode adicionar um botão de exportar PDF no relatório?",
                }
            ]
        }
    )

    content: str = Field(
        min_length=1,
        description="Message text sent to the assistant.",
    )


class MessageOut(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": "0191f3b2-4c3a-7b00-8000-000000000014",
                    "role": "assistant",
                    "content": "Claro! Adicionei um botão de exportar PDF no rodapé do relatório.",
                    "created_at": "2026-08-05T16:00:05Z",
                }
            ]
        },
    )

    id: UUID
    role: str = Field(description="'user' or 'assistant'")
    content: str
    created_at: BrDateTime


class MessagePage(BaseModel):
    """History page. `next_cursor` = id (UUID) of the oldest message in this
    page; pass it as `cursor` on the next call to fetch older ones
    (scroll up). `null` = beginning of the conversation reached."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "messages": [
                        {
                            "id": "0191f3b2-4c3a-7b00-8000-000000000014",
                            "role": "assistant",
                            "content": "Claro! Feito.",
                            "created_at": "2026-08-05T16:00:05Z",
                        },
                        {
                            "id": "0191f3b2-4c3a-7b00-8000-000000000013",
                            "role": "user",
                            "content": "Pode adicionar um botão de exportar PDF?",
                            "created_at": "2026-08-05T16:00:04Z",
                        },
                    ],
                    "next_cursor": "0191f3b2-4c3a-7b00-8000-000000000013",
                }
            ]
        }
    )

    messages: list[MessageOut]
    next_cursor: UUID | None


# ============================================================
# Artifacts (aninhados em /projects/{project_id}/artifacts)
# ============================================================


class ArtifactOut(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": "0191f3b2-4c3a-7b00-8000-00000000001e",
                    "filename": "serr-homolog-0.1.0(1).apk",
                    "size_bytes": 29413656,
                    "content_type": "application/vnd.android.package-archive",
                    "created_at": "2026-08-05T16:10:00Z",
                }
            ]
        },
    )

    id: UUID
    filename: str
    size_bytes: int = Field(description="Size in bytes")
    content_type: str | None
    created_at: BrDateTime


# ============================================================
# Auth (e-mail + senha → access + refresh tokens)
# ============================================================


class LoginRequest(BaseModel):
    """Logs in with e-mail + password."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"email": "samuelgadiel@gmail.com", "password": "••••••••••"}
            ]
        }
    )

    email: str = Field(
        min_length=3,
        max_length=255,
        description="E-mail cadastrado.",
        examples=["samuelgadiel@gmail.com"],
    )
    password: str = Field(
        min_length=6,
        max_length=128,
        description="Senha.",
        examples=["••••••••••"],
    )


class RefreshRequest(BaseModel):
    """Exchanges a refresh token for a new token pair (rotation)."""

    model_config = ConfigDict(
        json_schema_extra={"examples": [{"refresh_token": "abc123..."}]}
    )

    refresh_token: str = Field(
        description="Refresh token opaco retornado por login/refresh.",
        examples=["abc123..."],
    )


class LogoutRequest(BaseModel):
    """Revokes a refresh token (ends that device's session)."""

    model_config = ConfigDict(
        json_schema_extra={"examples": [{"refresh_token": "abc123..."}]}
    )

    refresh_token: str = Field(
        description="Refresh token da sessão a encerrar.",
        examples=["abc123..."],
    )


class UserOut(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": "0191f3b2-4c3a-7b00-8000-0000000000ff",
                    "email": "samuelgadiel@gmail.com",
                    "name": "Samuel Gadiel de Ávila",
                    "picture_url": None,
                    "role": "admin",
                    "status": "active",
                    "created_at": "2026-08-05T16:00:00Z",
                    "updated_at": "2026-08-05T16:00:00Z",
                }
            ]
        },
    )

    id: UUID
    email: str
    name: str
    picture_url: str | None
    role: str = Field(description="'admin' or 'member'")
    status: str = Field(description="'active', 'blocked' or 'deleted'")
    created_at: BrDateTime
    updated_at: BrDateTime


class LoginResponse(BaseModel):
    """Token pair + user profile."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "access_token": "eyJhbG...VCJ9...",
                    "refresh_token": "abc123...",
                    "token_type": "bearer",
                    "user": {
                        "id": "0191f3b2-4c3a-7b00-8000-0000000000ff",
                        "email": "samuelgadiel@gmail.com",
                        "name": "Samuel Gadiel de Ávila",
                        "picture_url": None,
                        "role": "admin",
                        "status": "active",
                        "created_at": "2026-08-05T16:00:00Z",
                        "updated_at": "2026-08-05T16:00:00Z",
                    },
                }
            ]
        }
    )

    access_token: str = Field(
        description="JWT de acesso (curto) — envie como `Authorization: Bearer <token>`."
    )
    refresh_token: str = Field(
        description="Token de refresh opaco (longo) — use em POST /auth/refresh."
    )
    token_type: str = Field(default="bearer")
    user: UserOut


# ============================================================
# Users (perfil do usuário autenticado)
# ============================================================


class UserUpdate(BaseModel):
    """Partial update of the current user's profile."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"name": "Samuel G.", "picture_url": "https://exemplo.com/foto.jpg"}
            ]
        }
    )

    name: str | None = Field(default=None, min_length=1, max_length=255)
    email: str | None = Field(default=None, min_length=3, max_length=255)
    picture_url: str | None = Field(default=None, max_length=1000)
    password: str | None = Field(
        default=None,
        min_length=6,
        max_length=128,
        description="Nova senha (opcional — troca a senha atual).",
    )
