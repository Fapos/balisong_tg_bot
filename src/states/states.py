from aiogram.fsm.state import default_state, State, StatesGroup
from enum import Enum


class OperationStates(Enum):
    email_added: int = 201
    email_exists: int = 202
    emails_preset_added: int = 203
    emails_preset_exists: int = 204
    emails_preset_not_exists: int = 205
    emails_preset_title_added: int = 206
    emails_preset_message_added: int = 207
    emails_preset_emails_added: int = 208
    emails_preset_emails_not_exists: int = 209
    emails_smtp_added: int = 210
    emails_smtp_not_exists: int = 211
    audio_added: int = 212
    audio_exists: int = 213

    something_wrong: int = 299


class ProfileStates(StatesGroup):
    profile_subscription_menu_state = State()


class EmailsStates(StatesGroup):
    emails_add_email_state = State()
    emails_add_preset_state = State()
    emails_add_list_emails_state = State()
    emails_notify_state = State()
    emails_presets_state = State()
    emails_settings_state = State()
    emails_show_list_state = State()
    emails_presets_settings_state = State()
    emails_presets_add_title = State()
    emails_presets_add_text = State()
    emails_presets_add_emails = State()
    emails_smtp_add_email = State()
    emails_smtp_add_password = State()
    emails_on_notify = State()
    emails_on_notify_select_preset = State()
    emails_on_notify_start = State()


class EmailsPaginationStates(StatesGroup):
    emails_pagination_next_state = State()
    emails_pagination_prev_state = State()


class AudioStates(StatesGroup):
    audio_add_file_state = State()
    audio_settings_state = State()


class VideoStates(StatesGroup):
    video_authorization_state = State()
    video_add_background_state = State()
    video_generate_state = State()
    video_settings_state = State()


class MenuStates(StatesGroup):
    main_menu_state = State()
    profile_menu_state = State()
    emails_menu_state = State()
    audio_menu_state = State()
    video_menu_state = State()
    tutor_menu_state = State()


class TutorialsStates(StatesGroup):
    tutorial_general_state = State()


class ApplyStates(StatesGroup):
    apply_emails_settings_state = State()
    apply_audio_settings_state = State()
    apply_video_settings_state = State()


MAIN_MENU_BACK_BUTTON_STATES = [
    MenuStates.profile_menu_state,
    MenuStates.emails_menu_state,
    MenuStates.audio_menu_state,
    MenuStates.video_menu_state,
    MenuStates.tutor_menu_state,
]


EMAILS_BACK_BUTTON_STATES = [
    EmailsStates.emails_show_list_state,
    EmailsStates.emails_settings_state,
    EmailsStates.emails_presets_state,
]


EMAILS_PRESETS_BACK_BUTTON_STATES = [
    EmailsStates.emails_presets_settings_state,
]


EMAILS_PRESETS_CANCEL_BUTTON_STATES = [
    EmailsStates.emails_add_preset_state,
]


EMAILS_PRESET_SETTINGS_CANCEL_BUTTON_STATES = [
    EmailsStates.emails_presets_add_title,
    EmailsStates.emails_presets_add_text,
    EmailsStates.emails_presets_add_emails,
]


EMAILS_CANCEL_BUTTON_STATES = [
    EmailsStates.emails_add_email_state,
    EmailsStates.emails_smtp_add_email,
    EmailsStates.emails_smtp_add_password,
    EmailsStates.emails_on_notify,
    EmailsStates.emails_on_notify_select_preset,
]

VIDEO_CANCEL_BUTTON_STATES = [
    VideoStates.video_authorization_state,
]


