from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

btn_main = KeyboardButton(text='Main menu')

# --- MAIN MENU ---
btn_settings = KeyboardButton(text='Settings')
btn_other = KeyboardButton(text='Other')

main_menu = ReplyKeyboardMarkup(keyboard=[[btn_settings], [btn_other], [btn_main]], resize_keyboard=True)

# --- OTHER MENU ---
btn_info = KeyboardButton(text='Info')
btn_profile = KeyboardButton(text='Profile')

other_menu = ReplyKeyboardMarkup(keyboard=[[btn_info], [btn_profile], [btn_main]], resize_keyboard=True)

# --- SETTINGS MENU ---
btn_add_email = KeyboardButton(text='Add target email')

settings_menu = ReplyKeyboardMarkup(keyboard=[[btn_add_email], [btn_main]])