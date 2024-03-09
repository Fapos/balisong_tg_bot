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


@router.callback_query()
async def process_not_implemented(callback: CallbackQuery, state: FSMContext):
    await callback.answer(
        text=LEXICON_RU['not_implemented'],
    )
