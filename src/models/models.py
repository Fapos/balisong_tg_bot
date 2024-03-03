from typing import List
from typing import Optional
from sqlalchemy import (
    ForeignKey, String, Text
)
from sqlalchemy.orm import (
    DeclarativeBase, Mapped,
    mapped_column, relationship,
    Session
)
from sqlalchemy import Engine, select, insert, update, delete, create_engine

from src.config_data.config import config


class Base(DeclarativeBase):
    pass


class Users(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    tid: Mapped[int] = mapped_column(unique=True, nullable=False)
    username: Mapped[str] = mapped_column(String(30), nullable=False)
    name: Mapped[str] = mapped_column(String(30))
    premium: Mapped[bool]

    emails_users_related: Mapped[list['Emails']] = relationship(
        back_populates='users_emails_related',
        secondary='emails_matching',
    )

    def __repr__(self) -> str:
        return f'User(id={self.id!r}, name={self.name!r}, fullname={self.premium!r})'


#  ----------------------------------------- EMAILS -------------------------------------------------------------------
class Emails(Base):
    __tablename__ = 'emails'

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)

    users_emails_related: Mapped[list['Users']] = relationship(
        back_populates='emails_users_related',
        secondary='emails_matching',
    )

    emails_presets_emails_related: Mapped[list['EmailsPresets']] = relationship(
        back_populates='emails_emails_presets_related',
        secondary='emails_list',
    )

    def __repr__(self) -> str:
        return f'Address(id={self.id!r}, email_address={self.email!r})'


class EmailsPresets(Base):
    __tablename__ = 'emails_presets'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.tid', ondelete='CASCADE'))
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    message_title: Mapped[str] = mapped_column(String(50), nullable=True)
    message_text: Mapped[str] = mapped_column(Text, nullable=True)

    emails_emails_presets_related: Mapped[list['Emails']] = relationship(
        back_populates='emails_presets_emails_related',
        secondary='emails_list',
    )

    def __repr__(self) -> str:
        return f''


class EmailsSMTP(Base):
    __tablename__ = 'emails_smtp'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.tid', ondelete='CASCADE'))
    email: Mapped[str] = mapped_column(String(50), nullable=False)
    password: Mapped[str] = mapped_column(String(50), nullable=False)

    def __repr__(self) -> str:
        return f''


class EmailsList(Base):
    __tablename__ = 'emails_list'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    preset_id: Mapped[int] = mapped_column(
        ForeignKey('emails_presets.id', ondelete='CASCADE'),
        primary_key=True,
    )
    email_id: Mapped[int] = mapped_column(
        ForeignKey('emails.id', ondelete='CASCADE'),
        primary_key=True,
    )

    def __repr__(self) -> str:
        return f''


class EmailsMatching(Base):
    __tablename__ = 'emails_matching'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey('users.tid', ondelete='CASCADE'),
        primary_key=True,
    )
    email_id: Mapped[int] = mapped_column(
        ForeignKey('emails.id', ondelete='CASCADE'),
        primary_key=True,
    )

    def __repr__(self) -> str:
        return f'EmailsMatching(user_id={self.user_id!r}, email_id={self.email_id!r})'


#  ----------------------------------------- AUDIOS -------------------------------------------------------------------
class Audios(Base):
    __tablename__ = 'audios'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String(50), nullable=False)

    users_related: Mapped[list['Users']] = relationship('Users')


engine = create_engine(
    f'postgresql+psycopg2://{config.db.db_user}:{config.db.db_password}@{config.db.db_host}/{config.db.database}',
    isolation_level="SERIALIZABLE",
)

Base().metadata.create_all(engine)
# Base().metadata.drop_all(engine)
