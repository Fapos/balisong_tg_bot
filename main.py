import asyncio
import html
import io
import logging
import sys

import aiogram
import aiosmtplib

import asyncio
import aiosmtplib
import sys
import psycopg2
import psycopg2.errors
import pyyoutube
import sqlalchemy.exc
from sqlalchemy.orm import Session, selectinload

import markups as nav
import database.db_model as db

from database.db_model import Users, Emails, EmailsMatching

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText



from aiogram import Bot, Dispatcher, Router, types, F
from aiogram.enums import ParseMode
from aiogram.filters import (
    CommandStart,
    Command,
    ChatMemberUpdatedFilter,
    IS_MEMBER,
    IS_NOT_MEMBER,
    Filter,
    StateFilter,
    MagicData,
)
from aiogram.filters.callback_data import CallbackData
from aiogram.types import Message, ContentType, ReplyKeyboardRemove, KeyboardButton, ReplyKeyboardMarkup, CallbackQuery, \
    ChatMemberUpdated, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.markdown import hbold
from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from typing import Any, Optional

from pathlib import Path

from sqlalchemy import Engine, select, insert, update, create_engine

from pyyoutube import Client, Api

from interface import interface as I

# Bot token can be obtained via https://t.me/BotFather
TOKEN = "6624666390:AAF6KfwUKoRkDp83PW-d8pxeyclVMYiBL6w"


class TelegramBot:
    def __init__(self):
        # All handlers should be attached to the Router (or Dispatcher)
        self.router = Router(name=__name__)
        self.storage = MemoryStorage()
        self.dp = Dispatcher(storage=self.storage)
        self.bot = Bot(TOKEN, parse_mode=ParseMode.HTML)
        self.dp.include_router(self.router)

        self.engine = create_engine(
            "postgresql+psycopg2://postgres:postgres@localhost/balisong_tg",
            isolation_level="SERIALIZABLE",
        )

        db.Base().metadata.create_all(self.engine)

        self.register_handlers()



    # Создаем свой класс фабрики коллбэков, указывая префикс
    # и структуру callback_data



    # Этот хэндлер будет срабатывать на команду /start
    # и отправлять пользователю сообщение с клавиатурой

    async def process_start_command(self, message: Message):
        await message.answer(
            text='Main menu',
            reply_markup=I.main_menu
        )

    async def show_main_menu(self, message: Message, state: FSMContext):
        await message.answer(
            text='Main menu',
            reply_markup=I.main_menu
        )

    async def show_settings_menu(self, message: Message, state: FSMContext):
        await message.answer(
            text='Settings menu',
            reply_markup=I.settings_menu
        )

    async def process_any_inline_button_press(self, callback: CallbackQuery, state: FSMContext):
        if await state.get_state() == 'BotMenu:settings_menu':
            await callback.message.edit_text(
                text='Settings menu',
                inline_message_id=callback.id,
                reply_markup=I.settings_menu,
            )
        # print(await state.get_state())
        if callback.data == 'menu:0:0:1':
            await callback.message.edit_text(
                text='Settings menu',
                inline_message_id=callback.id,
                reply_markup=I.settings_menu,
            )
        if callback.data == 'menu:1:0:0':
            await callback.message.edit_text(
                text='Main menu',
                inline_message_id=callback.id,
                reply_markup=I.main_menu,
            )
        if callback.data == 'states:1':
            await state.set_state(I.DefaultStates.email)
            await callback.message.edit_text(
                text='Enter target email',
                inline_message_id=callback.id,
                reply_markup=I.cancel,
            )

        if callback.data == 'states:0':
            await callback.message.edit_text(
                text='Main menu',
                inline_message_id=callback.id,
                reply_markup=I.main_menu,
            )
        # print(callback.model_dump_json(indent=4, exclude_none=True))
        await callback.answer()

    def register_handlers(self):
        """
        Регистрация обработчиков событий
        :return:
        """
        # Регистрация обработчиков событий от пользователя
        def _register_handlers_list(_register_def: Any, _callback: Any, _filters: Optional[list] = None):
            if _filters:
                for _filter in _filters:
                    if _filter:
                        _register_def(_callback, _filter)
                    else:
                        _register_def(_callback)
            else:
                _register_def(_callback)

        try:

            self.router.callback_query.register(
                self.process_any_inline_button_press,
            )
            self.router.message.register(
                self.process_start_command,
                CommandStart(),
            )
            self.router.message.register(
                self.show_settings_menu,
                StateFilter(I.BotMenu.settings_menu),
            )
            self.router.message.register(
                self.add_target_email,
                StateFilter(I.DefaultStates.email),
            )

            # Блокирование бота пользователем
            # _register_handlers_list(
            #     self.router.my_chat_member.register,
            #     self.on_user_leave,
            #     [
            #         ChatMemberUpdatedFilter(IS_MEMBER >> IS_NOT_MEMBER),
            #     ]
            # )
            # # Регистрация пользователя
            # _register_handlers_list(
            #     self.router.my_chat_member.register,
            #     self.on_user_join,
            #     [
            #         ChatMemberUpdatedFilter(IS_NOT_MEMBER >> IS_MEMBER),
            #     ]
            # )
            # # Авторизация пользователя
            # _register_handlers_list(
            #     self.router.my_chat_member.register,
            #     self.authorization_user,
            # )
            # # Отмена действия
            # _register_handlers_list(
            #     self.router.message.register,
            #     self.cancel_handler,
            #     [
            #         Command('cancel'),
            #         MagicData(F.text.casefold() == 'cancel'),
            #     ]
            # )
            # # Команда генерации и загрузки видео
            # _register_handlers_list(
            #     self.router.message.register,
            #     self.upload_video_handler,
            #     [
            #         Command('cancel'),
            #         Command('upload_video'),
            #     ]
            # )
            # # Обработка команды /start
            # _register_handlers_list(
            #     self.router.message.register,
            #     self.command_start_handler,
            #     [
            #         CommandStart(),
            #     ]
            # )
            # # Обработка вызова главного меню
            # _register_handlers_list(
            #     self.router.message.register,
            #     self.show_main_menu,
            #     [
            #         Command('menu'),
            #         MagicData(F.text.casefold() == 'main menu'),
            #     ]
            # )
            # # Обработка вызова меню опций
            # _register_handlers_list(
            #     self.router.message.register,
            #     self.show_settings_menu,
            #     [
            #         MagicData(F.text.casefold() == 'settings'),
            #         Command('settings'),
            #     ]
            # )

            # self.router.message.register(
            #     self.show_settings_menu,
            #     Command('settings'),
            #     F.data.casefold().__eq__('settings'),
            # )
            # # Обработка команды добавления почты
            # _register_handlers_list(
            #     self.router.message.register,
            #     self.set_add_target_email,
            #     [
            #         Command('add_target_email'),
            #         MagicData(F.text.casefold() == 'add target email'),
            #         StateFilter(EmailForm.email),
            #     ]
            # )
            # # Обработка загрузки аудиофайла
            # _register_handlers_list(
            #     self.router.message.register,
            #     self.audio_handler,
            #     [
            #         MagicData(F.audio),
            #     ]
            # )

            logging.info('Register handlers successful')
            for handler in self.router.message.handlers:
                print(handler)
        except Exception as exc:
            logging.error('Something wrong in register handlers', exc_info=exc)



    async def start(self):
        await self.dp.start_polling(self.bot)

    async def on_user_leave(self, event: ChatMemberUpdated):
        print(event.from_user.id)

    async def on_user_join(self, event: ChatMemberUpdated):
        with Session(self.engine) as session:
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

    async def authorization_user(self, user: types.ChatMemberUpdated) -> Any:
        print(user)

    async def cancel_handler(self, message: Message, state: FSMContext) -> None:
        current_state = await state.get_state()
        if current_state is None:
            return

        logging.info("Cancelling state %r", current_state)
        await state.clear()
        await message.answer(
            "Cancelled.",
            reply_markup=ReplyKeyboardRemove(),
        )

    def upload_video(self):
        from youtube_up import AllowCommentsEnum, Metadata, PrivacyEnum, YTUploaderSession

        yt_api = 'AIzaSyBQcp0lc6GjzKit2v64BZdIiN7VjxMyC8U'
        client = Client(api_key=yt_api)
        video = Path('files/test.mp4').read_bytes()

        uploader = YTUploaderSession.from_cookies_txt("cookies/cookies.txt")
        metadata = Metadata(
            title="Video title",
            description="Video description",
            privacy=PrivacyEnum.PUBLIC,
            made_for_kids=False,
            allow_comments_mode=AllowCommentsEnum.HOLD_ALL,
        )
        uploader.upload("video.webm", metadata)

    async def upload_video_handler(self, message: Message, state: FSMContext) -> None:
        self.upload_video()
        await message.answer(
            "Video uploaded.",
            reply_markup=ReplyKeyboardRemove(),
        )

    async def command_start_handler(self, message: Message, state: FSMContext) -> None:
        """
        This handler receives messages with `/start` command
        """
        # Most event objects have aliases for API methods that can be called in events' context
        # For example if you want to answer to incoming message you can use `message.answer()` alias
        # and the target chat will be passed to :ref:`aiogram.methods.send_message.SendMessage`
        # method automatically or call API method directly via
        # Bot instance: `bot.send_message(chat_id=message.chat.id, )`
        await state.clear()
        await state.set_state(BotMenu.main_menu)
        print(await state.get_state())
        await message.answer(f"Hello, {hbold(message.from_user.full_name)}!", reply_markup=nav.main_menu)

    async def add_target_email(self, message: Message, state: FSMContext):
            email = message.text

            with Session(self.engine) as session:
                try:
                    mail_ids = list(session.execute(select(Emails.id)).scalars().all())
                    try:
                        last_email_id = session.execute(select(Emails.id).where(Emails.email == email)).scalars().one()
                    except sqlalchemy.exc.NoResultFound:
                        last_email_id = max(mail_ids) + 1
                    print('mail_ids - ', mail_ids)
                    try:
                        check_exists = session.execute(
                            select(Emails.id)
                            .where(Emails.email == email)
                        ).scalars().one()
                    except sqlalchemy.exc.NoResultFound:
                        check_exists = None

                    try:
                        if check_exists:
                            check_matching_exists = session.execute(
                                select(EmailsMatching.email_id)
                                .where(EmailsMatching.user_id == message.from_user.id)
                                .where(EmailsMatching.email_id == last_email_id)
                            ).scalars().one()
                            print(last_email_id, check_matching_exists)
                        else:
                            check_matching_exists = None
                    except sqlalchemy.exc.NoResultFound:
                        check_matching_exists = None

                    print('results - ', check_exists, check_matching_exists)

                    new_email = Emails(
                        email=email,
                    )

                    if not check_exists:
                        session.add(new_email)
                        session.commit()
                        last_email_id = session.execute(select(Emails.id).where(Emails.email == email)).scalars().one()
                    else:
                        logging.info('Adding matching email. Username - %s' % message.from_user.username)
                        session.reset()
                        last_email_id = check_exists

                    new_matching = EmailsMatching(
                        user_id=message.from_user.id,
                        email_id=last_email_id,
                    )

                    if not check_matching_exists:
                        session.add(new_matching)
                        session.commit()
                        await message.answer(
                            'Email successfully added',
                            reply_markup=I.settings_menu,
                        )

                    else:
                        logging.info(
                            f'Matching email already exists. Username - {message.from_user.username}, email - {message.text}'
                        )
                        await message.answer(
                            'Email exists.',
                            reply_markup=I.settings_menu,
                        )
                finally:
                    await state.clear()

    async def audio_handler(self, message: types.Message):
        print(message.audio)
        file_id = message.audio.file_id
        file = await self.bot.get_file(file_id)
        print(file)
        file_path = file.file_path
        await self.bot.download_file(file_path, Path('files') / message.audio.file_name)


async def main() -> None:
    # Initialize Bot instance with a default parse mode which will be passed to all API calls

    # And the run events dispatching
    tg_bot = TelegramBot()
    await tg_bot.start()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
