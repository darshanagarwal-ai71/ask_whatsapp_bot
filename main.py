from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager, suppress
import datetime as dt
from functools import wraps
from urllib.parse import urlparse

from fastapi import FastAPI, Request
from pywa.api import WhatsAppError
from pywa_async import WhatsApp, filters
from pywa_async.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.ask_service import ASK71Client
from app.commands import HELP_COMMAND, HELP_COMMAND_RESPONSE, NEW_COMMAND, NEW_COMMAND_RESPONSE, START_COMMAND, START_COMMAND_RESPONSE
from app.config import get_settings
from app.database import db_manager, with_db_session
from app.error_handlers import handle_whatsapp_error, logger, universal_error_handler, with_error_handling
from app.models import User
from app.utils import markdown_to_whatsapp, split_message_for_whatsapp, with_typing_indicator


settings = get_settings()
parsed_webhook = urlparse(settings.webhook_url)
WEBHOOK_PATH = parsed_webhook.path or "/webhook"

SESSION_TIMEOUT = dt.timedelta(minutes=settings.session_timeout)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting FastAPI proxy layer")
    app.state.ask_client = ASK71Client(
        api_key=settings.ask_api_key,
        agent_id=settings.agent_id,
        api_url=settings.ask_api_base,
    )
    db_manager.init(settings.database_url)
    yield
    logger.info("Shutting down FastAPI proxy layer")
    await db_manager.close()
    await app.state.ask_client.close()

app = FastAPI(title="ASK WhatsApp Bot", lifespan=lifespan)

wa_client = WhatsApp(
    phone_id=settings.whatsapp_phone_id,
    token=settings.whatsapp_token,
    server=app,
    app_id=settings.whatsapp_app_id,
    app_secret=settings.whatsapp_app_secret,
    callback_url=settings.webhook_url,  
    verify_token=settings.verify_token,
    webhook_endpoint=WEBHOOK_PATH,
)



@wa_client.on_message(filters.text)
@with_error_handling
@with_typing_indicator
@with_db_session
async def handle_text_message(client: WhatsApp, msg: Message, db: AsyncSession) -> None:
    now = dt.datetime.now(dt.timezone.utc)
    wa_id = msg.from_user.wa_id
    username = msg.from_user.name
    text = msg.text.strip()
    await msg.mark_as_read()
    ask_client: ASK71Client = app.state.ask_client 

    user = await db.get(User, wa_id)

    if user is None:
        user = User(
            wa_id=wa_id,
            username=username,
            conversation_id=None,
            last_interaction=now,
        )
        db.add(user)

        await msg.reply_text(START_COMMAND_RESPONSE)
        await db.commit()
        return

    lower_text = text.lower()
    if lower_text == START_COMMAND:
        await msg.reply_text(START_COMMAND_RESPONSE)
        return

    if lower_text == NEW_COMMAND:
        user.conversation_id = None
        user.last_interaction = now
        user.username = username
        await db.commit()
        await msg.reply_text(NEW_COMMAND_RESPONSE)
        return
    if lower_text == HELP_COMMAND:
        await msg.reply_text(HELP_COMMAND_RESPONSE)
        return

    should_start_new = False
    if user.last_interaction is None:
        should_start_new = True
    else:
        should_start_new = now - user.last_interaction > SESSION_TIMEOUT

    conversation_id = None if should_start_new else user.conversation_id

    # ASK API call
    ask_response = await ask_client.send_query(
        query=text,
        conversation_id=conversation_id,
    )

    # Split message if it exceeds WhatsApp's character limit
    formatted_message = markdown_to_whatsapp(ask_response.message)
    message_chunks = split_message_for_whatsapp(formatted_message)
    
    for chunk in message_chunks:
        await msg.reply_text(chunk)

    user.conversation_id = ask_response.conversation_id
    user.last_interaction = now
    user.username = username
    await db.commit()



@app.get("/health")
async def healthcheck():
    return {"status": "ok"}

app.add_exception_handler(WhatsAppError, handle_whatsapp_error)
app.add_exception_handler(Exception, universal_error_handler)