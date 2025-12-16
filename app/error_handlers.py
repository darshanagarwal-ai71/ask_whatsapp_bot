from __future__ import annotations

import functools
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import HTTPException
from httpx import HTTPStatusError, Request
from pywa_async import WhatsApp
from pywa_async.api import WhatsAppError
from pywa_async.types import Message


logger = logging.getLogger(__name__)


def with_error_handling(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
    @functools.wraps(func)
    async def wrapper(client: WhatsApp, message: Message, *args: Any, **kwargs: Any) -> Any:
        try:
            return await func(client, message, *args, **kwargs)
        except WhatsAppError as exc:
            logger.error(
                "WhatsApp Bot error occurred: code=%s \n message=%s \n details=%s \n subcode=%s \n type=%s \n "
                "is_transient=%s \n fbtrace_id=%s \n href=%s \n user_title=%s \n user_msg=%s",
                exc.code,
                exc.message,
                exc.details,
                exc.subcode,
                exc.type,
                exc.is_transient,
                exc.fbtrace_id,
                exc.href,
                exc.user_title,
                exc.user_msg,
            )
            await client.send_message(
                to=message.from_user.wa_id,
                text="Sorry, something went wrong. Contact support.",
            )
        except HTTPStatusError as exc:
            logger.error("HTTP status error occurred: %s \n response body: %s", exc.response.status_code, exc.response.text)
            await client.send_message(
                to=message.from_user.wa_id,
                text="Sorry, something went wrong. Contact support.",
            )
        except HTTPException as exc:
            logger.error("HTTP exception occurred: %s \n response body: %s", exc.status_code, exc.detail)
            await client.send_message(
                to=message.from_user.wa_id,
                text="Sorry, something went wrong. Contact support.",
            )
    return wrapper


async def handle_whatsapp_error(exc: WhatsAppError):
    logger.error(
        "WhatsApp client error: code=%s \n message=%s \n details=%s \n subcode=%s \n type=%s \n "
        "is_transient=%s \n fbtrace_id=%s \n href=%s \n user_title=%s \n user_msg=%s",
        exc.code,
        exc.message,
        exc.details,
        exc.subcode,
        exc.type,
        exc.is_transient,
        exc.fbtrace_id,
        exc.href,
        exc.user_title,
        exc.user_msg,
    )

async def universal_error_handler(Request: Request, exc: Exception):
    logger.exception("Unhandled error: %s", exc)