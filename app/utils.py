import asyncio
from contextlib import suppress
from functools import wraps
import logging
import re
from contextlib import suppress

from pywa_async.types import Message

logger = logging.getLogger(__name__)

def markdown_to_whatsapp(text: str) -> str:
    """
    Converts basic Markdown formatting to WhatsApp formatting.

    This function handles the most common Markdown conversions:
    - Links: [text](url) -> text (url)
    - Bold: **text** -> *text*
    - Italic: *text* -> _text_
    - Strikethrough: ~~text~~ -> ~text~
    - Inline Code: `text` -> ```text```
    
    It assumes standard Markdown and does not handle nested or
    already-formatted WhatsApp strings (e.g., it will convert
    _italic_ to __italic__ if it's run twice, so apply it only once).
    """
    
    # 1. Convert Links: [text](url) -> text (url)
    # This regex finds [any text] followed by (any URL)
    # The (.*?) is a non-greedy match for the content.
    text = re.sub(r'\[(.*?)\]\((.*?)\)', r'\1 (\2)', text)
    
    # 2. Convert Bold: **text** -> *text*
    # This must run before the italic conversion.
    text = re.sub(r'\*\*(.*?)\*\*', r'*\1*', text)
    
    # 3. Convert Italic: *text* -> _text_
    # This runs after bold to avoid matching the * from bold.
    text = re.sub(r'\*(.*?)\*', r'_\1_', text)
    
    # 4. Convert Strikethrough: ~~text~~ -> ~text~
    text = re.sub(r'~~(.*?)~~', r'~\1~', text)
    
    # 5. Convert Inline Code: `text` -> ```text```
    # This regex handles single backticks.
    text = re.sub(r'`(.*?)`', r'```\1```', text)
    
    return text

def split_message_for_whatsapp(text: str, max_length: int = 4000) -> list[str]:
    """
    Splits a message into chunks suitable for WhatsApp's 4096 character limit.
    
    Args:
        text: The message to split
        max_length: Maximum length per chunk (default 4000 to stay under 4096 limit)
    
    Returns:
        List of message chunks
    
    Strategy:
        1. Split at nearest newline to max_length
        2. If no newline found, split at nearest period
        3. If no period found, split at max_length
    """
    if len(text) <= max_length:
        return [text]
    
    chunks = []
    remaining = text
    
    while len(remaining) > max_length:
        # Find the best split point
        split_point = max_length
        
        # Try to find a newline before max_length
        newline_idx = remaining.rfind('\n', 0, max_length)
        if newline_idx != -1:
            split_point = newline_idx + 1  # Include the newline
        else:
            # Try to find a period before max_length
            period_idx = remaining.rfind('.', 0, max_length)
            if period_idx != -1:
                split_point = period_idx + 1  # Include the period
        
        # Extract the chunk
        chunk = remaining[:split_point].strip()
        if chunk:
            chunks.append(chunk)
        
        # Update remaining text
        remaining = remaining[split_point:].strip()
    
    # Add any remaining text
    if remaining:
        chunks.append(remaining)
    
    return chunks


def with_typing_indicator(func):
    """Decorator that shows typing indicator while the function executes."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Extract the Message object from arguments
        async def typing_indicator_loop(msg: Message) -> None:
            """Continuously send typing action to keep indicator active."""
            try:
                while True:
                    await msg.indicate_typing()
                    await asyncio.sleep(25)
            except asyncio.CancelledError:
                pass
            except Exception as e:
                logger.exception(f"Typing indicator stopped unexpectedly: {e}")
        msg = None
        for arg in args:
            if isinstance(arg, Message):
                msg = arg
                break
        if msg is None:
            msg = kwargs.get('msg')
        
        if msg is None:
            # If no message found, just execute the function normally
            return await func(*args, **kwargs)
        
        typing_indicator_task = asyncio.create_task(typing_indicator_loop(msg))
        try:
            return await func(*args, **kwargs)
        finally:
            typing_indicator_task.cancel()
            with suppress(asyncio.CancelledError):
                await typing_indicator_task
    
    return wrapper