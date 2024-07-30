import json
import logging
from types import NoneType

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
    email_preset_settings_menu_default, back_menu, email_on_notify_audios, email_on_notify_start, profile_menu_default,
)
from src.services.audio_service import get_audio_list

from src.states.states import (
    MenuStates, EmailsStates,
    EmailsPaginationStates
)

from src.services.emails_service import add_target_email, get_emails_list, OperationStates, get_emails_presets_list, \
    add_new_preset, get_current_preset_message_title, add_message_title, get_current_preset_message_text, \
    add_message_text, add_preset_emails, get_current_preset_emails, get_current_smtp_settings, \
    set_current_smtp_settings, send_mail_async

router = Router()


@router.message(StateFilter(MenuStates.profile_menu_state))
async def process_main_menu_profile(ctx: Message, state: FSMContext):
    """
    Хендлер нажатия кнопки Профиль.

    :param ctx:
    :param state:
    :return:
    """
    keyboard = create_keyboard(*profile_menu_default)
    await state.set_state(MenuStates.profile_menu_state)
    await ctx.message.edit_text(
        text='PFKEGF',
        inline_message_id=ctx.id,
        reply_markup=keyboard,
    )