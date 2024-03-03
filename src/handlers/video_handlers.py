from aiogram import F, Router
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from src.keyboards.main_menu import create_web_app_keyboard

from src.states.states import (
    VideoStates
)

from src.services.video_utils.upload_video import upload, create_session
router = Router()


@router.callback_query(F.data == 'video_generate_and_upload_video_btn')
async def process_generate_and_upload_video(callback: CallbackQuery, state: FSMContext):
    """
    Хендлер нажатия кнопки Добавить почту.

    :param callback:
    :param state:
    :return:
    """
    _url = create_session(callback.from_user.id)
    keyboard = create_web_app_keyboard('auth_btn', 'Авторизация', _url)
    await state.set_state(VideoStates.video_authorization_state)
    await callback.message.edit_text(
        text='Авторизация',
        inline_message_id=callback.id,
        reply_markup=keyboard
    )