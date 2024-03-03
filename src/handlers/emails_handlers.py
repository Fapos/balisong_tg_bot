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
    email_preset_settings_menu_default, back_menu,
)

from src.states.states import (
    MenuStates, EmailsStates,
    EmailsPaginationStates
)

from src.services.emails_service import add_target_email, get_emails_list, OperationStates, get_emails_presets_list, \
    add_new_preset, get_current_preset_message_title, add_message_title, get_current_preset_message_text, \
    add_message_text, add_preset_emails, get_current_preset_emails, get_current_smtp_settings, set_current_smtp_settings

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
async def process_emails_email_presets_show(ctx: Union[CallbackQuery, Message], state: FSMContext):
    _presets = await get_emails_presets_list(ctx)
    await state.set_state(EmailsStates.emails_presets_state)
    keyboard = create_keyboard_from_dict(_presets, 'emails_presets_id', email_presets_menu_default)

    await ctx.message.edit_text(
        text=LEXICON_RU['emails_presets_label'],
        inline_message_id=ctx.id,
        reply_markup=keyboard,
    )


@router.callback_query(F.data.startswith('emails_presets_id'))
async def process_emails_email_presets_settings_show(ctx: CallbackQuery, state: FSMContext):
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
async def process_emails_add_message_title_query(ctx: CallbackQuery, state: FSMContext):
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
async def process_emails_add_message_title(ctx: Message, state: FSMContext):
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
async def process_emails_add_message_text_query(ctx: CallbackQuery, state: FSMContext):
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
async def process_emails_add_message_text(ctx: Message, state: FSMContext):
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
async def process_emails_add_emails_query(ctx: CallbackQuery, state: FSMContext):
    # TODO: Реализовать хендлер выбора почт для рассылки. Сделать пагинационный список кнопок с почтами
    # TODO: и возможность загрузить список почт в пресет
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
                    text=LEXICON_RU['emails_preset_message_added_label'],
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


@router.callback_query(F.data == 'emails_preset_add_emails_btn')
async def process_emails_select_file(ctx: CallbackQuery, state: FSMContext):
    # TODO: Реализовать хендлер отвечающий за выбор аудиофайла для рассылки
    # Выгрузить список добавленных аудиозаписей

    # Из списка сделать кнопки для выбора активного файла

    # Добавить название активного файла в БД
    ...


@router.callback_query(F.data == 'emails_on_notify_btn')
async def process_emails_on_notify(ctx: CallbackQuery, state: FSMContext):
    """
    Хендлер нажатия кнопки Включить рассылку.

    :param ctx:
    :param state:
    :return:
    """
    # TODO: Реализовать хендлер для активации рассылки
    # Проверка наличия в кеше списка почт

    # Выгрузить список почт по необходимости

    # Выгрузить тему и текст сообщения, название активного файла

    # Для каждой почты: провалидировать, вызвать send_mail_async и добавить в gather

    # Вывести на экран сообщение: Сообщения отправлены,
    # посмотреть результат можно в отправленных, на сайте той почты, которую вы используете
    keyboard = create_keyboard(*cancel_menu)
    await state.set_state(EmailsStates.emails_settings_state)
    await ctx.message.edit_text(
        text=LEXICON_RU['emails_settings_label'],
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
