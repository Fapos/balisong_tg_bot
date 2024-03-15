import json
import logging

import aioredis
from datetime import datetime
from typing import Union
from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from src.keyboards.main_menu import create_keyboard, create_keyboard_from_dict, create_keyboard_tuple
from src.lexicon.lexicon_ru import LEXICON_RU

from src.keyboards.menu_buttons import (
    email_menu_default, email_list_menu_default, cancel_menu, email_presets_menu_default,
    email_preset_settings_menu_default, back_menu, audio_menu_default,
)
from src.services.audio_service import add_audiofile

from src.states.states import (
    MenuStates, EmailsStates,
    EmailsPaginationStates, AudioStates
)

from src.services.emails_service import add_target_email, get_emails_list, OperationStates, get_emails_presets_list, \
    add_new_preset, get_current_preset_message_title, add_message_title, get_current_preset_message_text, \
    add_message_text, add_preset_emails, get_current_preset_emails, get_current_smtp_settings, set_current_smtp_settings

router = Router()


@router.callback_query(F.data == 'audio_add_audiofile_btn')
async def process_audio_add_audiofile_query(callback: CallbackQuery, state: FSMContext):
    """
    Хендлер нажатия кнопки Добавить почту.

    :param callback:
    :param state:
    :return:
    """
    keyboard = create_keyboard(*cancel_menu)
    await state.set_state(AudioStates.audio_add_file_state)
    await callback.message.edit_text(
        text=LEXICON_RU['audio_add_audiofile_label'],
        inline_message_id=callback.id,
        reply_markup=keyboard,
    )


@router.message(StateFilter(AudioStates.audio_add_file_state))
async def process_audio_add_audiofile(ctx: Message, state: FSMContext):
    """
    Хендлер, обрабатывающий отпарвку аудиофайла.

    :param ctx:
    :param state:
    :return:
    """
    keyboard = create_keyboard(*audio_menu_default)
    try:
        result = await add_audiofile(ctx)
        if result == OperationStates.audio_added:
            await ctx.answer(
                text=LEXICON_RU['audio_add_audiofile_successful_label'],
            )
        if result == OperationStates.audio_exists:
            await ctx.answer(
                text=LEXICON_RU['audio_add_audiofile_already_exists_label'],
            )
    except Exception as exc:
        await ctx.answer(
            text=LEXICON_RU['some_error_label'],
        )
        logging.error('Something wrong from audiofile adding', exc_info=exc)
    await state.set_state(MenuStates.audio_menu_state)
    await ctx.answer(
        text=LEXICON_RU['audio_title'],
        reply_markup=keyboard,
    )
