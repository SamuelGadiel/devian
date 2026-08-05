from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

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
                    "default_branch": "main",
                    "container_path": "/workspace/sisvisa-serr-mobile",
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
    default_branch: str = Field(
        default="main",
        description="Branch used by default in builds.",
        examples=["main"],
    )
    container_path: str | None = Field(
        default=None,
        description=(
            "Directory inside the `devian` container where Claude Code runs. "
            "Makes Claude load the project layer (CLAUDE.md / .claude)."
        ),
        examples=["/workspace/sisvisa-serr-mobile"],
    )


class ProjectUpdate(BaseModel):
    """Partial update — send only the fields you want to change."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "default_branch": "develop",
                }
            ]
        }
    )

    name: str | None = Field(default=None, min_length=1, max_length=100)
    repo_url: str | None = None
    default_branch: str | None = None
    container_path: str | None = None


class ProjectOut(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": 1,
                    "name": "sisvisa",
                    "repo_url": "git@bitbucket.org:branef/sisvisa-serr-mobile.git",
                    "default_branch": "main",
                    "container_path": "/workspace/sisvisa-serr-mobile",
                    "created_at": "2026-08-04T21:44:03.305361Z",
                }
            ]
        },
    )

    id: int
    name: str
    repo_url: str | None
    default_branch: str
    container_path: str | None
    created_at: datetime


# ============================================================
# Chats
# ============================================================


class ChatCreate(BaseModel):
    """Opens a new chat inside a project."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "project_id": 1,
                    "name": "nova-feature",
                }
            ]
        }
    )

    project_id: int = Field(
        description="ID of the project the chat belongs to.",
        examples=[1],
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
                    "id": 1,
                    "project_id": 1,
                    "name": "qual-a-cor",
                    "branch": "main",
                    "status": "active",
                    "created_at": "2026-08-04T21:44:08.958822Z",
                    "updated_at": "2026-08-04T21:44:12.366232Z",
                }
            ]
        },
    )

    id: int
    project_id: int
    name: str
    branch: str
    status: str
    created_at: datetime
    updated_at: datetime


# ============================================================
# Messages
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
                    "id": 4,
                    "role": "assistant",
                    "content": "Claro! Adicionei um botão de exportar PDF no rodapé do relatório.",
                    "created_at": "2026-08-04T21:44:12.366232Z",
                }
            ]
        },
    )

    id: int
    role: str = Field(description="'user' or 'assistant'")
    content: str
    created_at: datetime


class MessagePage(BaseModel):
    """History page. `next_cursor` = id of the oldest message in this page;
    pass it as `cursor` on the next call to fetch older ones (scroll up).
    `null` = beginning of the conversation reached."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "messages": [
                        {
                            "id": 4,
                            "role": "assistant",
                            "content": "Claro! Feito.",
                            "created_at": "2026-08-04T21:44:12.366232Z",
                        },
                        {
                            "id": 3,
                            "role": "user",
                            "content": "Pode adicionar um botão de exportar PDF?",
                            "created_at": "2026-08-04T21:44:12.361597Z",
                        },
                    ],
                    "next_cursor": 3,
                }
            ]
        }
    )

    messages: list[MessageOut]
    next_cursor: int | None


# ============================================================
# Artifacts
# ============================================================


class ArtifactOut(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": 1,
                    "filename": "serr-homolog-0.1.0(1).apk",
                    "size_bytes": 29413656,
                    "content_type": "application/vnd.android.package-archive",
                    "created_at": "2026-08-04T21:44:36.951372Z",
                }
            ]
        },
    )

    id: int
    filename: str
    size_bytes: int = Field(description="Size in bytes")
    content_type: str | None
    created_at: datetime
