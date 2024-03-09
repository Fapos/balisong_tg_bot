import psycopg2
import psycopg2.errors
import logging
import sqlalchemy
from pathlib import Path

from aiogram.types import ChatMemberUpdated

from src.models.models import *


def on_user_join(event: ChatMemberUpdated):
    with Session(engine) as session:
        new_user = Users(
            tid=event.from_user.id,
            username=event.from_user.username,
            name=event.from_user.full_name,
            premium=False,
        )
        try:
            session.add(new_user)
            session.commit()
        except (psycopg2.errors.UniqueViolation, psycopg2.errors.IntegrityError, sqlalchemy.exc.IntegrityError) as exc:
            logging.info('Update user data. Username - %s' % event.from_user.username)
            session.reset()
            stmt = select(Users).where(Users.tid == event.from_user.id)
            user = session.scalars(stmt).one()
            user.username = event.from_user.username
            user.name = event.from_user.full_name
            session.commit()


        Path(f'trashbox/{event.from_user.id}/creds').mkdir(exist_ok=True, parents=True)
        Path(f'trashbox/{event.from_user.id}/audios').mkdir(exist_ok=True, parents=True)
        Path(f'trashbox/{event.from_user.id}/video').mkdir(exist_ok=True, parents=True)
        Path(f'trashbox/{event.from_user.id}/images').mkdir(exist_ok=True, parents=True)
        Path(f'trashbox/{event.from_user.id}/presets').mkdir(exist_ok=True, parents=True)