from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Projeto(Base):
    __tablename__ = "projetos"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    repo_url: Mapped[str] = mapped_column(String(500))
    branch_padrao: Mapped[str] = mapped_column(String(100), default="main")
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    sessoes: Mapped[list["Sessao"]] = relationship(back_populates="projeto")


class Sessao(Base):
    __tablename__ = "sessoes"

    id: Mapped[int] = mapped_column(primary_key=True)
    chat_id_app: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    session_id_claude: Mapped[str] = mapped_column(String(100), unique=True)
    projeto_id: Mapped[int | None] = mapped_column(
        ForeignKey("projetos.id"), nullable=True
    )
    branch: Mapped[str] = mapped_column(String(100), default="main")
    status: Mapped[str] = mapped_column(String(20), default="ativa")
    criada_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    projeto: Mapped[Projeto | None] = relationship(back_populates="sessoes")
    mensagens: Mapped[list["Mensagem"]] = relationship(
        back_populates="sessao", cascade="all, delete-orphan"
    )


class Mensagem(Base):
    __tablename__ = "mensagens"

    id: Mapped[int] = mapped_column(primary_key=True)
    sessao_id: Mapped[int] = mapped_column(ForeignKey("sessoes.id"))
    role: Mapped[str] = mapped_column(String(20))
    conteudo: Mapped[str] = mapped_column(Text)
    criada_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    sessao: Mapped[Sessao] = relationship(back_populates="mensagens")


class Build(Base):
    __tablename__ = "builds"

    id: Mapped[int] = mapped_column(primary_key=True)
    sessao_id: Mapped[int] = mapped_column(ForeignKey("sessoes.id"))
    run_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pendente")
    artifact_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
