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
    email_preset_settings_menu_default, back_menu, email_on_notify_audios, email_on_notify_start,
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


@router.callback_query(F.data == 'emails_add_email_btn')
async def process_emails_add_email_query(callback: CallbackQuery, state: FSMContext):
    """
    Хендлер нажатия кнопки Добавить почту.

    :param callback:
    :param state:
    :return:
    """
    keyboard = create_keyboard(*cancel_menu)
    await state.set_state(EmailsStates.emails_add_email_state)
    await callback.message.edit_text(
        text=LEXICON_RU['emails_add_email_label'],
        inline_message_id=callback.id,
        reply_markup=keyboard,
    )


@router.message(StateFilter(EmailsStates.emails_add_email_state))
async def process_emails_add_email(ctx: Message, state: FSMContext):
    """
    Хендлер, обрабатывающий ввод почты.

    :param ctx:
    :param state:
    :return:
    """
    if isinstance(ctx.text, str):
        keyboard = create_keyboard(*email_menu_default)
        try:
            result = await add_target_email(ctx)
            if result == OperationStates.email_added:
                await ctx.answer(
                    text=LEXICON_RU['emails_add_successful_label'],
                )
            if result == OperationStates.email_exists:
                await ctx.answer(
                    text=LEXICON_RU['emails_already_exists_label'],
                )
        except Exception as exc:
            await ctx.answer(
                text=LEXICON_RU['emails_some_error_label'],
            )
            logging.error('Something wrong from email adding', exc_info=exc)
        await state.set_state(MenuStates.emails_menu_state)
        await ctx.answer(
            text=LEXICON_RU['emails_add_email_label'],
            reply_markup=keyboard,
        )


@router.callback_query(F.data == 'emails_list_btn')
async def process_emails_list_query(ctx: CallbackQuery, state: FSMContext):
    """
    Хендлер нажатия кнопки Показать список почт.

    :param ctx:
    :param state:
    :return:
    """
    # keyboard = create_keyboard(*email_list_menu_default)
    redis = await aioredis.from_url('redis://127.0.0.1', db=0)
    await state.set_state(EmailsStates.emails_show_list_state)

    _emails = await get_emails_list(ctx)
    if _emails:
        await redis.set(f'{ctx.from_user.id}_emails_list', str(_emails))
        await redis.set(f'{ctx.from_user.id}_emails_list_page', 0)
        await redis.close()
        buttons_list = '\n'.join([*_emails[0]])
        keyboard = create_keyboard_tuple(
            [
                (_emails[0], 1),
                (['pagination_prev_btn', f'1/{len(_emails)}', 'pagination_next_btn', *back_menu], 3)
            ]
        )
        await ctx.message.edit_text(
            text=LEXICON_RU['emails_list_label'],
            inline_message_id=ctx.id,
            reply_markup=keyboard,
        )
    else:
        await ctx.message.answer(
            text=LEXICON_RU['emails_list_empty_label']
        )
        keyboard = create_keyboard(
            *email_menu_default
        )
        await ctx.message.answer(
            text=LEXICON_RU['emails_title'],
            inline_message_id=ctx.id,
            reply_markup=keyboard,
        )


@router.callback_query(
    F.data == 'pagination_next_btn'
)
async def process_emails_list_next(ctx: CallbackQuery, state: FSMContext):
    """
    Хендлер нажатия кнопки следующей страницы.

    :param ctx:
    :param state:
    :return:
    """
    curr_state = await state.get_state()

    redis = await aioredis.from_url('redis://127.0.0.1', db=0)

    if curr_state == EmailsStates.emails_show_list_state:
        _cur_page = int(await redis.get(f'{ctx.from_user.id}_emails_list_page'))
        _emails_str = bytes.decode(await redis.get(f'{ctx.from_user.id}_emails_list'), encoding='utf-8')
        _emails = json.loads(_emails_str.replace('\'', '"'))
        if _cur_page + 1 < len(_emails):
            _cur_page += 1
            buttons_list = '\n'.join([*_emails[_cur_page]])
            keyboard = create_keyboard_tuple(
                [
                    (_emails[_cur_page], 1),
                    (['pagination_prev_btn', f'{_cur_page + 1}/{len(_emails)}', 'pagination_next_btn', *back_menu], 3)
                ]
            )
            await ctx.message.edit_text(
                text=LEXICON_RU['emails_list_label'],
                inline_message_id=ctx.id,
                reply_markup=keyboard,
            )
            await redis.set(f'{ctx.from_user.id}_emails_list_page', _cur_page)
    await redis.close()


@router.callback_query(
    F.data == 'pagination_prev_btn'
)
async def process_emails_list_prev(ctx: CallbackQuery, state: FSMContext):
    """
    Хендлер нажатия кнопки предыдущей страницы.

    :param ctx:
    :param state:
    :return:
    """
    await state.set_state(EmailsStates.emails_show_list_state)

    redis = await aioredis.from_url('redis://127.0.0.1', db=0)
    _cur_page = int(await redis.get(f'{ctx.from_user.id}_emails_list_page'))
    _emails_str = bytes.decode(await redis.get(f'{ctx.from_user.id}_emails_list'), encoding='utf-8')
    _emails = json.loads(_emails_str.replace('\'', '"'))
    if _cur_page - 1 >= 0:
        _cur_page -= 1
        buttons_list = '\n'.join([*_emails[_cur_page]])
        keyboard = create_keyboard_tuple(
            [
                (_emails[_cur_page], 1),
                (['pagination_prev_btn', f'{_cur_page + 1}/{len(_emails)}', 'pagination_next_btn', *back_menu], 3)
            ]
        )
        await ctx.message.edit_text(
            text=LEXICON_RU['emails_list_label'],
            inline_message_id=ctx.id,
            reply_markup=keyboard,
        )
        await redis.set(f'{ctx.from_user.id}_emails_list_page', _cur_page)

    await redis.close()


@router.callback_query(F.data == 'emails_preset_add_preset_btn')
async def process_emails_add_preset_query(ctx: CallbackQuery, state: FSMContext):
    keyboard = create_keyboard(*cancel_menu)
    await state.set_state(EmailsStates.emails_add_preset_state)

    await ctx.message.edit_text(
        text=LEXICON_RU['emails_add_preset_label'],
        inline_message_id=ctx.id,
        reply_markup=keyboard,
    )


@router.message(StateFilter(EmailsStates.emails_add_preset_state))
async def process_emails_add_preset(ctx: Message, state: FSMContext):
    """
    Хендлер, обрабатывающий ввод имени пресета.

    :param ctx:
    :param state:
    :return:
    """
    if isinstance(ctx.text, str):
        try:
            result = await add_new_preset(ctx)
            if result == OperationStates.emails_preset_added:
                await ctx.answer(
                    text=LEXICON_RU['emails_add_preset_successfully_label'],
                )
            if result == OperationStates.emails_preset_exists:
                await ctx.answer(
                    text=LEXICON_RU['emails_add_preset_exists_label'],
                )
        except Exception as exc:
            logging.error('[add_email_preset] Something wrong', exc_info=exc)
            await ctx.answer(
                text=LEXICON_RU['emails_some_error_label'],
            )
        await state.set_state(EmailsStates.emails_presets_state)
        _presets = await get_emails_presets_list(
            CallbackQuery(
                id='111',
                from_user=ctx.from_user,
                message=ctx,
                chat_instance=str(ctx.chat.id),
            )
        )
        keyboard = create_keyboard_from_dict(_presets, 'emails_presets_id', email_presets_menu_default)
        await ctx.answer(
            text=LEXICON_RU['emails_add_preset_label'],
            reply_markup=keyboard,
        )


@router.callback_query(F.data == 'emails_email_presets_btn')
async def process_emails_presets_show(ctx: Union[CallbackQuery, Message], state: FSMContext):
    _presets = await get_emails_presets_list(ctx)
    await state.set_state(EmailsStates.emails_presets_state)
    keyboard = create_keyboard_from_dict(_presets, 'emails_presets_id', email_presets_menu_default)

    await ctx.message.edit_text(
        text=LEXICON_RU['emails_presets_label'],
        inline_message_id=ctx.id,
        reply_markup=keyboard,
    )


@router.callback_query(F.data.startswith('emails_presets_id'))
async def process_emails_presets_settings_show(ctx: CallbackQuery, state: FSMContext):
    await state.set_state(EmailsStates.emails_presets_settings_state)
    keyboard = create_keyboard(*email_preset_settings_menu_default)
    redis = await aioredis.from_url('redis://127.0.0.1', db=0)
    await redis.set(f'{ctx.from_user.id}_current_email_preset_id', ctx.data.split(":")[1])
    await redis.set(f'{ctx.from_user.id}_current_email_preset_name', ctx.data.split(":")[2])
    await redis.close()

    await ctx.message.edit_text(
        text=LEXICON_RU['emails_presets_settings_label'] + f' {ctx.data.split(":")[2]}',
        inline_message_id=ctx.id,
        reply_markup=keyboard,
    )
    print(ctx.data)


@router.callback_query(F.data == 'emails_preset_add_message_title_btn')
async def process_emails_preset_add_message_title_query(ctx: CallbackQuery, state: FSMContext):
    keyboard = create_keyboard(*cancel_menu)
    await state.set_state(EmailsStates.emails_presets_add_title)
    redis = await aioredis.from_url('redis://127.0.0.1', db=0)

    preset_id = int(bytes.decode(await redis.get(f'{ctx.from_user.id}_current_email_preset_id'), encoding='utf-8'))
    current_title = await get_current_preset_message_title(ctx, preset_id)
    if current_title:
        msg = (LEXICON_RU['emails_preset_title_curr_label'] + '\n' +
               current_title + '\n' + LEXICON_RU['emails_preset_title_none_label'])
    else:
        msg = LEXICON_RU['emails_preset_title_none_label']
    await ctx.message.edit_text(
        text=msg,
        inline_message_id=ctx.id,
        reply_markup=keyboard,
    )


@router.message(StateFilter(EmailsStates.emails_presets_add_title))
async def process_emails_preset_add_message_title(ctx: Message, state: FSMContext):
    if isinstance(ctx.text, str):
        keyboard = create_keyboard(*email_preset_settings_menu_default)
        redis = await aioredis.from_url('redis://127.0.0.1', db=0)

        preset_id = int(bytes.decode(await redis.get(f'{ctx.from_user.id}_current_email_preset_id'), encoding='utf-8'))
        try:
            result = await add_message_title(ctx, preset_id)
            if result == OperationStates.emails_preset_title_added:
                await ctx.answer(
                    text=LEXICON_RU['emails_preset_title_added_label'],
                )
        except Exception as exc:
            logging.error('[add_email_preset] Something wrong', exc_info=exc)
            await ctx.answer(
                text=LEXICON_RU['some_error_label'],
            )
        await state.set_state(EmailsStates.emails_presets_settings_state)
        await ctx.answer(
            text=LEXICON_RU['emails_add_preset_label'],
            reply_markup=keyboard,
        )


@router.callback_query(F.data == 'emails_preset_add_message_text_btn')
async def process_emails_preset_add_message_text_query(ctx: CallbackQuery, state: FSMContext):
    keyboard = create_keyboard(*cancel_menu)
    await state.set_state(EmailsStates.emails_presets_add_text)
    redis = await aioredis.from_url('redis://127.0.0.1', db=0)

    preset_id = int(bytes.decode(await redis.get(f'{ctx.from_user.id}_current_email_preset_id'), encoding='utf-8'))
    current_text = await get_current_preset_message_text(ctx, preset_id)
    if current_text:
        msg = (LEXICON_RU['emails_preset_message_curr_label'] + '\n' +
               current_text + '\n' + LEXICON_RU['emails_preset_message_none_label'])
    else:
        msg = LEXICON_RU['emails_preset_message_none_label']
    await ctx.message.edit_text(
        text=msg,
        inline_message_id=ctx.id,
        reply_markup=keyboard,
    )


@router.message(StateFilter(EmailsStates.emails_presets_add_text))
async def process_emails_preset_add_message_text(ctx: Message, state: FSMContext):
    if isinstance(ctx.text, str):
        keyboard = create_keyboard(*email_preset_settings_menu_default)
        redis = await aioredis.from_url('redis://127.0.0.1', db=0)

        preset_id = int(bytes.decode(await redis.get(f'{ctx.from_user.id}_current_email_preset_id'), encoding='utf-8'))
        try:
            result = await add_message_text(ctx, preset_id)
            if result == OperationStates.emails_preset_message_added:
                await ctx.answer(
                    text=LEXICON_RU['emails_preset_message_added_label'],
                )
        except Exception as exc:
            logging.error('[add_email_preset] Something wrong', exc_info=exc)
            await ctx.answer(
                text=LEXICON_RU['some_error_label'],
            )
        await state.set_state(EmailsStates.emails_presets_settings_state)
        await ctx.answer(
            text=LEXICON_RU['emails_add_preset_label'],
            reply_markup=keyboard,
        )


@router.callback_query(F.data == 'emails_preset_add_emails_btn')
async def process_emails_preset_add_emails_query(ctx: CallbackQuery, state: FSMContext):
    keyboard = create_keyboard(*cancel_menu)
    await state.set_state(EmailsStates.emails_presets_add_emails)
    redis = await aioredis.from_url('redis://127.0.0.1', db=0)

    preset_id = int(bytes.decode(await redis.get(f'{ctx.from_user.id}_current_email_preset_id'), encoding='utf-8'))
    current_text = await get_current_preset_emails(ctx, preset_id)
    emails = '\n'.join([
        email for email in current_text
    ])
    if emails:
        msg = (LEXICON_RU['emails_preset_emails_curr_label'] + '\n' +
               emails + '\n' + LEXICON_RU['emails_preset_emails_none_label'])
    else:
        msg = LEXICON_RU['emails_preset_emails_none_label']
    await ctx.message.edit_text(
        text=msg,
        inline_message_id=ctx.id,
        reply_markup=keyboard,
    )


@router.callback_query(F.data == 'emails_set_smtp_settings_btn')
async def process_emails_smtp_settings_query(ctx: CallbackQuery, state: FSMContext):
    keyboard = create_keyboard(*cancel_menu)

    email = await get_current_smtp_settings(ctx)
    if email:
        msg = (LEXICON_RU['emails_smtp_curr_label'] + '\n' +
               email + '\n' + LEXICON_RU['emails_smtp_email_add_label'])
    else:
        msg = (LEXICON_RU['emails_smtp_none_label'] + '\n' +
               LEXICON_RU['emails_smtp_email_add_label'])

    await state.set_state(EmailsStates.emails_smtp_add_email)
    await ctx.message.edit_text(
        text=msg,
        inline_message_id=ctx.id,
        reply_markup=keyboard,
    )


@router.message(StateFilter(EmailsStates.emails_smtp_add_email))
async def process_emails_smtp_add_email(ctx: Message, state: FSMContext):
    if isinstance(ctx.text, str):
        keyboard = create_keyboard(*cancel_menu)
        redis = await aioredis.from_url('redis://127.0.0.1', db=0)
        await redis.set(f'{ctx.from_user.id}_smtp_email', ctx.text.strip())
        await state.set_state(EmailsStates.emails_smtp_add_password)
        await ctx.answer(
            text=LEXICON_RU['emails_smtp_password_add_label'],
            reply_markup=keyboard,
        )


@router.message(StateFilter(EmailsStates.emails_smtp_add_password))
async def process_emails_smtp_add_password(ctx: Message, state: FSMContext):
    if isinstance(ctx.text, str):
        keyboard = create_keyboard(*email_menu_default)
        await state.set_state(MenuStates.emails_menu_state)

        redis = await aioredis.from_url('redis://127.0.0.1', db=0)
        email = bytes.decode(await redis.get(f'{ctx.from_user.id}_smtp_email'), encoding='utf-8')

        try:
            result = await set_current_smtp_settings(ctx, email, ctx.text.strip())
            if result == OperationStates.emails_smtp_added:
                await ctx.answer(
                    text=LEXICON_RU['emails_smtp_added_label'],
                )
        except Exception as exc:
            logging.error('[add_email_smtp] Something wrong', exc_info=exc)
            await ctx.answer(
                text=LEXICON_RU['some_error_label'],
            )
        await ctx.answer(
            text=LEXICON_RU['emails_title'],
            reply_markup=keyboard,
        )


@router.message(StateFilter(EmailsStates.emails_presets_add_emails))
async def process_emails_add_emails(ctx: Message, state: FSMContext):
    if isinstance(ctx.text, str):
        keyboard = create_keyboard(*email_preset_settings_menu_default)
        redis = await aioredis.from_url('redis://127.0.0.1', db=0)

        preset_id = int(
            bytes.decode(await redis.get(f'{ctx.from_user.id}_current_email_preset_id'), encoding='utf-8'))
        try:
            result = await add_preset_emails(ctx, preset_id)
            if result == OperationStates.emails_preset_emails_added:
                await ctx.answer(
                    text=LEXICON_RU['emails_preset_emails_added_label'],
                )
        except Exception as exc:
            logging.error('[add_email_preset_emails] Something wrong', exc_info=exc)
            await ctx.answer(
                text=LEXICON_RU['some_error_label'],
            )
        await state.set_state(EmailsStates.emails_presets_settings_state)
        await ctx.answer(
            text=LEXICON_RU['emails_add_preset_label'],
            reply_markup=keyboard,
        )


@router.callback_query(F.data == 'emails_on_notify_btn')
async def process_emails_on_notify(ctx: CallbackQuery, state: FSMContext):
    """
    Хендлер нажатия кнопки Включить рассылку.

    :param ctx:
    :param state:
    :return:
    """
    _smtp_settings = await get_current_smtp_settings(ctx)
    if not _smtp_settings:
        await ctx.message.edit_text(
            text=LEXICON_RU['emails_smtp_none_label'],
            inline_message_id=ctx.id,
        )
        keyboard = create_keyboard(*email_menu_default)
        await ctx.message.answer(
            text=LEXICON_RU['emails_title'],
            reply_markup=keyboard,
        )
        return

    _audios = await get_audio_list(ctx)
    print(_audios)
    if isinstance(_audios, dict):
        redis = await aioredis.from_url('redis://127.0.0.1', db=0)
        _json_dumps = json.dumps(_audios)
        await redis.set(f'{ctx.from_user.id}_audios_list', _json_dumps)
        await redis.delete(f'{ctx.from_user.id}_checked_audios_list')
        await redis.close()
        await state.set_state(EmailsStates.emails_on_notify)
        keyboard = create_keyboard_from_dict(_audios, 'emails_audios_id', email_on_notify_audios)

        await ctx.message.edit_text(
            text=LEXICON_RU['emails_audios_list_label'],
            inline_message_id=ctx.id,
            reply_markup=keyboard,
        )
    else:
        keyboard = create_keyboard(*email_menu_default)
        await ctx.message.edit_text(
            text=LEXICON_RU['emails_audios_list_empty_label'],
            inline_message_id=ctx.id,
            reply_markup=keyboard,
        )


@router.callback_query(F.data.startswith('emails_audios_id'))
async def process_emails_audios_generate_list(ctx: CallbackQuery, state: FSMContext):
    redis = await aioredis.from_url('redis://127.0.0.1', db=0)
    _audio_list = bytes.decode(await redis.get(f'{ctx.from_user.id}_audios_list'), encoding='utf-8')
    _audios = json.loads(_audio_list)
    _checked_raw = await redis.get(f'{ctx.from_user.id}_checked_audios_list')
    if not isinstance(_checked_raw, NoneType):
        _checked_audios_list = bytes.decode(_checked_raw, encoding='utf-8')
        _checked_audios = json.loads(_checked_audios_list)
    else:
        _checked_audios = {}

    if ctx.data.split(':')[1] in _checked_audios:
        _audios[ctx.data.split(':')[1]] = ctx.data.split(':')[2].replace('+ ', '')
        _checked_audios.pop(ctx.data.split(':')[1])
    else:
        _audios[ctx.data.split(':')[1]] = '+ ' + ctx.data.split(':')[2]
        _checked_audios[ctx.data.split(':')[1]] = ctx.data.split(':')[2]

    # Продолжить добавление
    await redis.set(f'{ctx.from_user.id}_audios_list', json.dumps(_audios))
    await redis.set(f'{ctx.from_user.id}_checked_audios_list', json.dumps(_checked_audios))
    keyboard = create_keyboard_from_dict(_audios, 'emails_audios_id', email_on_notify_audios)

    await redis.set(f'{ctx.from_user.id}_current_email_preset_name', ctx.data.split(":")[2])
    await redis.close()

    await ctx.message.edit_text(
        text=LEXICON_RU['emails_audios_selected_label'] + '\n' + '\n'.join(_checked_audios.values()),
        inline_message_id=ctx.id,
        reply_markup=keyboard,
    )


@router.callback_query(F.data == 'accept_btn')
async def process_emails_on_notify_select_preset_query(ctx: CallbackQuery, state: FSMContext):
    """
    Хендлер нажатия кнопки Применить в рассылке.

    :param ctx:
    :param state:
    :return:
    """
    redis = await aioredis.from_url('redis://127.0.0.1', db=0)
    _checked_raw = await redis.get(f'{ctx.from_user.id}_checked_audios_list')
    if isinstance(_checked_raw, NoneType):
        await ctx.answer(LEXICON_RU['emails_audios_selected_empty_label'])
        return

    await state.set_state(EmailsStates.emails_on_notify_select_preset)
    print(await state.get_state())
    _presets = await get_emails_presets_list(ctx)
    if isinstance(_presets, dict) and _presets:
        keyboard = create_keyboard_from_dict(_presets, 'emails_notify_preset_id', cancel_menu)

        await ctx.message.edit_text(
            text=LEXICON_RU['emails_preset_list_label'],
            inline_message_id=ctx.id,
            reply_markup=keyboard,
        )
    else:
        keyboard = create_keyboard(*cancel_menu)
        await ctx.message.edit_text(
            text=LEXICON_RU['emails_preset_list_empty_label'],
            inline_message_id=ctx.id,
            reply_markup=keyboard,
        )


@router.callback_query(F.data.startswith('emails_notify_preset_id'))
async def process_emails_audios_generate_list(ctx: CallbackQuery, state: FSMContext):
    await state.set_state(EmailsStates.emails_on_notify)
    redis = await aioredis.from_url('redis://127.0.0.1', db=0)
    _audio_list = bytes.decode(await redis.get(f'{ctx.from_user.id}_audios_list'), encoding='utf-8')
    _audios = json.loads(_audio_list)
    _checked_raw = await redis.get(f'{ctx.from_user.id}_checked_audios_list')
    if not isinstance(_checked_raw, NoneType):
        _checked_audios_list = bytes.decode(_checked_raw, encoding='utf-8')
        _checked_audios = json.loads(_checked_audios_list)
    else:
        _checked_audios = {}

    keyboard = create_keyboard(*email_on_notify_start)

    await redis.set(f'{ctx.from_user.id}_current_email_preset_id', ctx.data.split(":")[1])
    await redis.close()

    _message = (
        LEXICON_RU['emails_notify_on_label']
        .replace('%PRESET_NAME%', ctx.data.split(':')[2])
        .replace('%FILE_LIST%', '\n'.join(_checked_audios.values()))
    )
    await ctx.message.edit_text(
        text=_message,
        inline_message_id=ctx.id,
        reply_markup=keyboard,
    )


@router.callback_query(F.data == 'start_notify_btn')
async def process_emails_on_notify_start(ctx: CallbackQuery, state: FSMContext):
    """
    Хендлер нажатия кнопки Применить в рассылке.

    :param ctx:
    :param state:
    :return:
    """
    redis = await aioredis.from_url('redis://127.0.0.1', db=0)
    _checked_raw = await redis.get(f'{ctx.from_user.id}_checked_audios_list')
    if not isinstance(_checked_raw, NoneType):
        _checked_audios_list = bytes.decode(_checked_raw, encoding='utf-8')
        _checked_audios = json.loads(_checked_audios_list)
    else:
        _checked_audios = {}

    _preset = await redis.get(f'{ctx.from_user.id}_current_email_preset_id')
    try:
        print(list(_checked_audios.values()))
        result = await send_mail_async(ctx, int(_preset), list(_checked_audios.values()))
        print(result)

        if result:
            if result == OperationStates.emails_preset_emails_not_exists:
                await ctx.message.answer(
                    text=LEXICON_RU['emails_preset_email_list_empty_label'],
                )
            if result == OperationStates.emails_preset_not_exists:
                await ctx.message.answer(
                    text=LEXICON_RU['emails_preset_not_setting_label'],
                )
            keyboard = create_keyboard(*email_menu_default)
            await ctx.message.answer(
                text=LEXICON_RU['emails_title'],
                inline_message_id=ctx.id,
                reply_markup=keyboard,
            )
            return

        await ctx.message.answer(
            text=LEXICON_RU['emails_notify_on_start'],
        )

    except Exception as exc:
        logging.error('[on_notify] Something wrong', exc_info=exc)
        await ctx.message.answer(
            text=LEXICON_RU['some_error_label'],
        )

    keyboard = create_keyboard(*email_menu_default)
    await ctx.message.answer(
        text=LEXICON_RU['emails_title'],
        inline_message_id=ctx.id,
        reply_markup=keyboard,
    )


@router.callback_query(F.data == 'emails_set_smtp_settings_btn')
async def process_emails_show_settings(ctx: CallbackQuery, state: FSMContext):
    """
    Хендлер нажатия кнопки Добавить почту.

    :param ctx:
    :param state:
    :return:
    """
    keyboard = create_keyboard(*cancel_menu)
    await state.set_state(EmailsStates.emails_settings_state)
    await ctx.message.edit_text(
        text=LEXICON_RU['emails_smtp_add_label'],
        inline_message_id=ctx.id,
        reply_markup=keyboard,
    )
