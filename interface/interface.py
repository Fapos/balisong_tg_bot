from aiogram.filters.callback_data import CallbackData
from aiogram.types import Message, ContentType, ReplyKeyboardRemove, KeyboardButton, ReplyKeyboardMarkup, CallbackQuery, \
    ChatMemberUpdated, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.markdown import hbold
from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext


class DefaultStates(StatesGroup):
    email = State()


class BotMenu(StatesGroup):
    main_menu = State()
    other_menu = State()
    settings_menu = State()


class MenuCallbackFactory(CallbackData, prefix='menu'):
    main_menu: bool
    other_menu: bool
    settings_menu: bool


class DefaultStatesFactory(CallbackData, prefix='states'):
    email: bool


# Создаем объекты кнопок, с применением фабрики коллбэков
main_btn = InlineKeyboardButton(
    text='Main menu',
    callback_data=MenuCallbackFactory(
        main_menu=True,
        other_menu=False,
        settings_menu=False,
    ).pack()
)

settings_btn = InlineKeyboardButton(
    text='Settings',
    callback_data=MenuCallbackFactory(
        main_menu=False,
        other_menu=False,
        settings_menu=True,
    ).pack()
)

other_btn = InlineKeyboardButton(
    text='Other',
    callback_data=MenuCallbackFactory(
        main_menu=False,
        other_menu=True,
        settings_menu=False,
    ).pack()
)

add_email_btn = InlineKeyboardButton(
    text='Add target email',
    callback_data=DefaultStatesFactory(
        email=True,
    ).pack()
)

cancel_btn = InlineKeyboardButton(
    text='Cancel',
    callback_data=DefaultStatesFactory(
        email=False,
    ).pack()
)


# Создаем объект клавиатуры, добавляя в список списки с кнопками
main_menu = InlineKeyboardMarkup(
    inline_keyboard=[[settings_btn], [other_btn]]
)

settings_menu = InlineKeyboardMarkup(
    inline_keyboard=[[add_email_btn], [main_btn]]
)

cancel = InlineKeyboardMarkup(
    inline_keyboard=[[cancel_btn]]
)