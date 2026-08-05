from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.timezones import UtcDateTime

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
                    "created_at": "2026-08-05T19:00:00Z",
                    "updated_at": "2026-08-05T19:00:00Z",
                }
            ]
        },
    )

    id: UUID
    name: str
    repo_url: str | None
    branch: str
    created_at: UtcDateTime
    updated_at: UtcDateTime


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
                    "branch": "develop",
                    "status": "active",
                    "created_at": "2026-08-05T19:00:00Z",
                    "updated_at": "2026-08-05T19:00:05Z",
                }
            ]
        },
    )

    id: UUID
    project_id: UUID
    name: str
    branch: str
    status: str
    created_at: UtcDateTime
    updated_at: UtcDateTime


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
                    "created_at": "2026-08-05T19:00:05Z",
                }
            ]
        },
    )

    id: UUID
    role: str = Field(description="'user' or 'assistant'")
    content: str
    created_at: UtcDateTime


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
                            "created_at": "2026-08-05T19:00:05Z",
                        },
                        {
                            "id": "0191f3b2-4c3a-7b00-8000-000000000013",
                            "role": "user",
                            "content": "Pode adicionar um botão de exportar PDF?",
                            "created_at": "2026-08-05T19:00:04Z",
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
                    "created_at": "2026-08-05T19:10:00Z",
                }
            ]
        },
    )

    id: UUID
    filename: str
    size_bytes: int = Field(description="Size in bytes")
    content_type: str | None
    created_at: UtcDateTime
