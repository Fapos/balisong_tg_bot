from typing import Optional

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder
from src.lexicon.lexicon_ru import LEXICON_RU


# Функция, генерирующая клавиатуру для страницы книги
def create_keyboard(*buttons: str, _width: Optional[int] = 1) -> InlineKeyboardMarkup:
    # Инициализируем билдер
    kb_builder = InlineKeyboardBuilder()
    # Добавляем в билдер ряд с кнопками
    kb_builder.row(*[InlineKeyboardButton(
        text=LEXICON_RU[button] if button in list(LEXICON_RU.keys()) else button,
        callback_data=button) for button in buttons],
        width=_width,
    )
    # Возвращаем объект инлайн-клавиатуры
    return kb_builder.as_markup()


def create_keyboard_tuple(buttons: list) -> InlineKeyboardMarkup:
    # Инициализируем билдер
    kb_builder = InlineKeyboardBuilder()
    # Добавляем в билдер ряд с кнопками
    for tpl in buttons:
        print(tpl)
        kb_builder.row(*[InlineKeyboardButton(
            text=LEXICON_RU[button] if button in list(LEXICON_RU.keys()) else button,
            callback_data=button) for button in tpl[0]],
            width=tpl[1],
        )
    # Возвращаем объект инлайн-клавиатуры
    return kb_builder.as_markup()


def create_keyboard_from_dict(
        buttons: dict,
        _callback_data: str,
        list_buttons: Optional[list] = list,
        _width: Optional[int] = 1
) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру из словаря.

    :param buttons: Словарь типа {идентификатор для коллбека: текст кнопки}
    :param _callback_data: Токен для коллбека будет возвращаться как: {callback_data}_{button_id}
    :param list_buttons: Список дополнительных кнопок
    :param _width: Ширина клавиатуры в кнопках
    :return:
    """
    kb_builder = InlineKeyboardBuilder()
    _buttons = [
        *[
            InlineKeyboardButton(
                text=_text,
                callback_data=f'{_callback_data}:{_id}:{_text}'
            ) for _id, _text in buttons.items()
        ],
        *[
            InlineKeyboardButton(
                text=LEXICON_RU[button] if button in list(LEXICON_RU.keys()) else button,
                callback_data=button
            ) for button in list_buttons
        ]
    ]
    # Добавляем в билдер ряд с кнопками
    kb_builder.row(
        *_buttons,
        width=_width,
    )
    # Возвращаем объект инлайн-клавиатуры
    return kb_builder.as_markup()


def create_web_app_keyboard(button: str, text: str, _url: str) -> InlineKeyboardMarkup:
    # Инициализируем билдер
    kb_builder = InlineKeyboardBuilder()
    # Добавляем в билдер ряд с кнопками
    web_app_info = WebAppInfo(url=_url)
    kb_builder.row(*[
        InlineKeyboardButton(
            text=text,
            web_app=web_app_info
            ),
        InlineKeyboardButton(
            text=LEXICON_RU['cancel_btn'],
            callback_data='cancel_btn'
        )
        ],
       width=1,
    )
    # Возвращаем объект инлайн-клавиатуры
    return kb_builder.as_markup()
