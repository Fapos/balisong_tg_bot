import logging
import os
import sqlalchemy.exc
from pathlib import Path

from aiogram.types import Message, CallbackQuery

from src.config_data.config import bot
from src.states.states import OperationStates
from src.models.models import *


async def add_audiofile(ctx: Message):
    _user_id = ctx.from_user.id
    try:
        with Session(engine) as session:
            try:
                _data = session.execute(
                    select(Audios.id)
                    .where(Audios.user_id == _user_id)
                    .where(Audios.name == ctx.audio.file_name)
                )
                _audiofile = _data.scalars().one()
                return OperationStates.audio_exists
            except sqlalchemy.exc.NoResultFound:
                _audiofile = None

            file_id = ctx.audio.file_id
            file = await bot.get_file(file_id)
            file_path = file.file_path
            await bot.download_file(file_path, Path(f'./trashbox/{ctx.from_user.id}/audios') / ctx.audio.file_name)

            new_audio = Audios(
                user_id=_user_id,
                name=ctx.audio.file_name,
            )

            session.add(new_audio)
            session.commit()
        return OperationStates.audio_added
    except Exception as exc:
        logging.error('[add_audiofile] Something wrong in adding audiofile', exc_info=exc)
        raise


async def get_audio_list(ctx: CallbackQuery):
    _user_id = ctx.from_user.id

    with Session(engine) as session:
        try:
            _data = session.execute(
                select(Audios.id, Audios.name)
                .where(Audios.user_id == _user_id)
            )
            _result = list(_data.tuples().all())
            for i in range(0, len(_result)):
                _result[i] = (str(_result[i][0]), _result[i][1])
            _result = dict(_result)
        except sqlalchemy.exc.NoResultFound:
            _result = None

    return _result
