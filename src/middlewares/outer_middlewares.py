import logging
from typing import Any, Awaitable, Callable, Dict
from datetime import datetime

import aioredis
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from src.utils.utils import get_redis

logger = logging.getLogger(__name__)


class CheckKeyboardLifetimeOuterMiddleware(BaseMiddleware):
    # TODO: Доделать проверку времени жизни клавиатуры
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        redis = await get_redis()
        try:
            last_update = await redis.get(f'{event.from_user.id}_last_keyboard_update')
        except KeyError:
            ...

        datetime.now().isoformat(timespec='seconds')
        result = await handler(event, data)

        logger.debug('Выходим из миддлвари  %s', __class__.__name__)

        return result
