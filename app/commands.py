from app.config import get_settings

settings = get_settings()


START_COMMAND = "/start"
NEW_COMMAND = "/new"
HELP_COMMAND = "/help"

START_COMMAND_RESPONSE = (
    f"Welcome to the ASK WhatsApp Bot.\n\n"
    "Available commands: \n\t/new to start a new conversation \n"
    "\t/help to get help \n\n"
    f"Note: conversation will be closed after {settings.session_timeout} minutes if no activity the next message would start a new conversation\n\n"
    "Ask your question"
)

NEW_COMMAND_RESPONSE = "Started a new conversation. Ask your question."

HELP_COMMAND_RESPONSE = (
    "Available commands: \n\t/new to start a new conversation \n"
    "\t/help to get help \n\n"
    f"Note: conversation will be closed after {settings.session_timeout} minutes if no activity the next message would start a new conversation"
)