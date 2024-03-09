import logging
from pathlib import Path

import aioredis
import psycopg2.errors
import sqlalchemy.exc
from aiogram import Router
from aiogram.filters import CommandStart, ChatMemberUpdatedFilter, IS_NOT_MEMBER, IS_MEMBER
from aiogram.types import Message, ChatMemberUpdated
from aiogram.fsm.context import FSMContext
from sqlalchemy.orm import Session

from src.keyboards.main_menu import create_keyboard
from src.lexicon.lexicon_ru import LEXICON_RU

from src.keyboards.menu_buttons import (
    main_menu_default,
)
from src.models.models import *

from src.states.states import (
    MenuStates,
)
router = Router()


# Этот хэндлер будет срабатывать на команду "/start" -
# добавлять пользователя в базу данных, если его там еще не было
# и отправлять ему приветственное сообщение


@router.message(CommandStart())
async def process_start_command(ctx: Message, state: FSMContext):
    """
    Хендлер команды /start

    :param ctx:
    :param state:
    :return:
    """

    with Session(engine) as session:
        new_user = Users(
            tid=ctx.from_user.id,
            username=ctx.from_user.username,
            name=ctx.from_user.full_name,
            premium=False,
        )
        try:
            session.add(new_user)
            session.commit()
            logging.info('Added user. Username - %s' % ctx.from_user.username)
        except (psycopg2.errors.UniqueViolation, psycopg2.errors.IntegrityError, sqlalchemy.exc.IntegrityError) as exc:
            logging.info('Update user data. Username - %s' % ctx.from_user.username)
            session.reset()
            stmt = select(Users).where(Users.tid == ctx.from_user.id)
            user = session.scalars(stmt).one()
            user.username = ctx.from_user.username
            user.name = ctx.from_user.full_name
            session.commit()

    Path(f'./trashbox/{ctx.from_user.id}/creds').mkdir(exist_ok=True, parents=True)
    Path(f'./trashbox/{ctx.from_user.id}/audios').mkdir(exist_ok=True, parents=True)
    Path(f'./trashbox/{ctx.from_user.id}/video').mkdir(exist_ok=True, parents=True)
    Path(f'./trashbox/{ctx.from_user.id}/profiles').mkdir(exist_ok=True, parents=True)

    keyboard = create_keyboard(*main_menu_default)
    await state.set_state(MenuStates.main_menu_state)
    await ctx.answer(
        text=LEXICON_RU['main_menu_title'],
        reply_markup=keyboard,
    )


@router.my_chat_member(ChatMemberUpdatedFilter(IS_NOT_MEMBER >> IS_MEMBER))
async def process_on_user_join(event: ChatMemberUpdated):
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

    Path(f'/trashbox/{event.from_user.id}/creds').mkdir(exist_ok=True, parents=True)
    Path(f'/trashbox/{event.from_user.id}/audios').mkdir(exist_ok=True, parents=True)
    Path(f'/trashbox/{event.from_user.id}/video').mkdir(exist_ok=True, parents=True)
    Path(f'/trashbox/{event.from_user.id}/profiles').mkdir(exist_ok=True, parents=True)

