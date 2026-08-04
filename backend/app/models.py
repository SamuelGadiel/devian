from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Projeto(Base):
    __tablename__ = "projetos"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    repo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    branch_padrao: Mapped[str] = mapped_column(String(100), default="main")
    caminho_container: Mapped[str | None] = mapped_column(String(500), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    chats: Mapped[list["Chat"]] = relationship(
        back_populates="projeto", cascade="all, delete-orphan"
    )
    artefatos: Mapped[list["Artefato"]] = relationship(
        back_populates="projeto", cascade="all, delete-orphan"
    )


class Chat(Base):
    __tablename__ = "chats"

    id: Mapped[int] = mapped_column(primary_key=True)
    projeto_id: Mapped[int] = mapped_column(
        ForeignKey("projetos.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(100), default="novo-chat")
    session_id_claude: Mapped[str] = mapped_column(String(100), unique=True)
    branch: Mapped[str] = mapped_column(String(100), default="main")
    status: Mapped[str] = mapped_column(String(20), default="ativa")
    criada_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    atualizada_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    projeto: Mapped[Projeto] = relationship(back_populates="chats")
    mensagens: Mapped[list["Mensagem"]] = relationship(
        back_populates="chat", cascade="all, delete-orphan"
    )


class Mensagem(Base):
    __tablename__ = "mensagens"

    id: Mapped[int] = mapped_column(primary_key=True)
    chat_id: Mapped[int] = mapped_column(
        ForeignKey("chats.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[str] = mapped_column(String(20))
    conteudo: Mapped[str] = mapped_column(Text)
    criada_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    chat: Mapped[Chat] = relationship(back_populates="mensagens")


class Artefato(Base):
    __tablename__ = "artefatos"

    id: Mapped[int] = mapped_column(primary_key=True)
    projeto_id: Mapped[int] = mapped_column(
        ForeignKey("projetos.id", ondelete="CASCADE"), index=True
    )
    nome_arquivo: Mapped[str] = mapped_column(String(255))
    tamanho: Mapped[int] = mapped_column(Integer, default=0)
    content_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    projeto: Mapped[Projeto] = relationship(back_populates="artefatos")
