import logging
from pathlib import Path

import aioredis
import psycopg2.errors
import sqlalchemy.exc
from aiogram import Router
from aiogram.filters import CommandStart, ChatMemberUpdatedFilter, IS_NOT_MEMBER, IS_MEMBER
from aiogram.types import Message, ChatMemberUpdated
from aiogram.fsm.context import FSMContext
from sqlalchemy.orm import Session

from src.keyboards.main_menu import create_keyboard
from src.lexicon.lexicon_ru import LEXICON_RU

from src.keyboards.menu_buttons import (
    main_menu_default,
)
from src.models.models import *

from src.states.states import (
    MenuStates,
)
router = Router()

