import json

import aioredis
from aiogram import F, Router
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from src.config_data.config import config_ex
from src.keyboards.main_menu import create_keyboard, create_keyboard_from_dict, create_web_app_keyboard
from src.lexicon.lexicon_ru import LEXICON_RU

from src.utils.utils import get_redis

from src.keyboards.menu_buttons import (
    main_menu_default, profile_menu_default,
    email_menu_default, audio_menu_default,
    video_menu_default, cancel_menu, email_presets_menu_default, email_preset_settings_menu_default,
    tutorials_menu_default,
)
from src.services.emails_service import get_emails_presets_list

from src.states.states import (
    MenuStates, ProfileStates,
    EmailsStates, AudioStates,
    VideoStates, ApplyStates, EMAILS_BACK_BUTTON_STATES, MAIN_MENU_BACK_BUTTON_STATES, EMAILS_CANCEL_BUTTON_STATES,
    VIDEO_CANCEL_BUTTON_STATES, EMAILS_PRESETS_BACK_BUTTON_STATES, EMAILS_PRESETS_CANCEL_BUTTON_STATES,
    EMAILS_PRESET_SETTINGS_CANCEL_BUTTON_STATES
)

router = Router()


@router.callback_query(F.data == 'back_btn')
async def process_back_click(ctx: CallbackQuery, state: FSMContext):
    """
    Хендлер нажатия кнопки Назад.

    :param ctx:
    :param state:
    :return:
    """
    if await state.get_state() in MAIN_MENU_BACK_BUTTON_STATES:
        keyboard = create_keyboard(*main_menu_default)
        await state.set_state(MenuStates.main_menu_state)
        await ctx.message.edit_text(
            text=LEXICON_RU['main_menu_title'],
            inline_message_id=ctx.id,
            reply_markup=keyboard,
        )

    if await state.get_state() in EMAILS_BACK_BUTTON_STATES:
        keyboard = create_keyboard(*email_menu_default)
        await state.set_state(MenuStates.emails_menu_state)
        await ctx.message.edit_text(
            text=LEXICON_RU['emails_title'],
            inline_message_id=ctx.id,
            reply_markup=keyboard,
        )

    if await state.get_state() in EMAILS_PRESETS_BACK_BUTTON_STATES:
        await state.set_state(EmailsStates.emails_presets_state)
        _presets = await get_emails_presets_list(ctx)

        keyboard = create_keyboard_from_dict(_presets, 'emails_presets_id', email_presets_menu_default)
        await ctx.message.edit_text(
            text=LEXICON_RU['emails_presets_label'],
            inline_message_id=ctx.id,
            reply_markup=keyboard,
        )


@router.callback_query(F.data == 'cancel_btn')
async def process_cancel_click(ctx: CallbackQuery, state: FSMContext):
    """
    Хендлер нажатия кнопки Отмена.

    :param ctx:
    :param state:
    :return:
    """
    if await state.get_state() in EMAILS_CANCEL_BUTTON_STATES:
        keyboard = create_keyboard(*email_menu_default)
        await state.set_state(MenuStates.emails_menu_state)
        await ctx.message.edit_text(
            text=LEXICON_RU['emails_title'],
            inline_message_id=ctx.id,
            reply_markup=keyboard,
        )

    if await state.get_state() in EMAILS_PRESETS_CANCEL_BUTTON_STATES:
        await state.set_state(EmailsStates.emails_presets_state)
        _presets = await get_emails_presets_list(ctx)
        keyboard = create_keyboard_from_dict(_presets, 'emails_presets_id', email_presets_menu_default)
        await ctx.message.edit_text(
            text=LEXICON_RU['emails_presets_label'],
            inline_message_id=ctx.id,
            reply_markup=keyboard,
        )

    if await state.get_state() in EMAILS_PRESET_SETTINGS_CANCEL_BUTTON_STATES:
        await state.set_state(EmailsStates.emails_presets_settings_state)
        redis = await get_redis()
        preset_name = bytes.decode(await redis.get(f'{ctx.from_user.id}_current_email_preset_name'), encoding='utf-8')
        await redis.close()
        keyboard = create_keyboard(*email_preset_settings_menu_default)
        await ctx.message.edit_text(
            text=LEXICON_RU['emails_presets_settings_label'] + f' {preset_name}',
            inline_message_id=ctx.id,
            reply_markup=keyboard,
        )

    if await state.get_state() in VIDEO_CANCEL_BUTTON_STATES:
        keyboard = create_keyboard(*video_menu_default)
        await state.set_state(MenuStates.video_menu_state)
        await ctx.message.edit_text(
            text=LEXICON_RU['video_title'],
            inline_message_id=ctx.id,
            reply_markup=keyboard,
        )


@router.callback_query(F.data == 'main_menu_profile_btn')
async def process_main_menu_profile_click(ctx: CallbackQuery, state: FSMContext):
    """
    Хендлер нажатия кнопки Профиль.

    :param ctx:
    :param state:
    :return:
    """
    keyboard = create_keyboard(*profile_menu_default)
    await state.set_state(MenuStates.profile_menu_state)
    await ctx.message.edit_text(
        text=LEXICON_RU['profile_title'],
        inline_message_id=ctx.id,
        reply_markup=keyboard,
    )
    await ctx.answer()


@router.callback_query(F.data == 'main_menu_emails_btn')
async def process_main_menu_emails_click(ctx: CallbackQuery, state: FSMContext):
    """
    Хендлер нажатия кнопки Почты.

    :param ctx:
    :param state:
    :return:
    """
    keyboard = create_keyboard(*email_menu_default)
    await state.set_state(MenuStates.emails_menu_state)
    await ctx.message.edit_text(
        text=LEXICON_RU['emails_title'],
        inline_message_id=ctx.id,
        reply_markup=keyboard,
    )


@router.callback_query(F.data == 'main_menu_audio_btn')
async def process_main_menu_audio_click(ctx: CallbackQuery, state: FSMContext):
    """
    Хендлер нажатия кнопки аудио.

    :param ctx:
    :param state:
    :return:
    """
    keyboard = create_keyboard(*audio_menu_default)
    await state.set_state(MenuStates.audio_menu_state)
    await ctx.message.edit_text(
        text=LEXICON_RU['audio_title'],
        inline_message_id=ctx.id,
        reply_markup=keyboard,
    )


@router.callback_query(F.data == 'main_menu_video_btn')
async def process_main_menu_video_click(ctx: CallbackQuery, state: FSMContext):
    """
    Хендлер нажатия кнопки Видео.

    :param ctx:
    :param state:
    :return:
    """
    keyboard = create_keyboard(*video_menu_default)
    await state.set_state(MenuStates.video_menu_state)
    await ctx.message.edit_text(
        text=LEXICON_RU['video_title'],
        inline_message_id=ctx.id,
        reply_markup=keyboard,
    )


@router.callback_query(F.data == 'main_menu_tutors_btn')
async def process_main_menu_tutors_click(ctx: CallbackQuery, state: FSMContext):
    """
    Хендлер нажатия кнопки Как пользоваться ботом.

    :param ctx:
    :param state:
    :return:
    """
    buttons = config_ex['tutorial_links']
    keyboard = create_web_app_keyboard(buttons)
    await state.set_state(MenuStates.tutor_menu_state)
    await ctx.message.edit_text(
        text=LEXICON_RU['tutors_menu_title'],
        inline_message_id=ctx.id,
        reply_markup=keyboard,
    )