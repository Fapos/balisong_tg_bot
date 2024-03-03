from typing import List
from typing import Optional
from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship


class Base(DeclarativeBase):
    pass


class Users(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    tid: Mapped[int] = mapped_column(unique=True, nullable=False)
    username: Mapped[str] = mapped_column(String(30), nullable=False)
    name: Mapped[str] = mapped_column(String(30))
    premium: Mapped[bool]

    emails_matched: Mapped[list['Emails']] = relationship(
        back_populates='users_matched',
        secondary='emails_matching',
    )

    def __repr__(self) -> str:
        return f'User(id={self.id!r}, name={self.name!r}, fullname={self.premium!r})'


class Emails(Base):
    __tablename__ = 'emails'

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)

    users_matched: Mapped[list['Users']] = relationship(
        back_populates='emails_matched',
        secondary='emails_matching',
    )

    def __repr__(self) -> str:
        return f'Address(id={self.id!r}, email_address={self.email!r})'


class EmailsMatching(Base):
    __tablename__ = 'emails_matching'

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
