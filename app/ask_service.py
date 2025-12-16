"""
ASK71 API client for streaming requests
"""
from fastapi import HTTPException, status
import httpx
import json
import logging
import time
from typing import Optional, Dict, Any, Tuple, AsyncGenerator
from httpx_sse import aconnect_sse

logger = logging.getLogger(__name__)


class ASK71Response:
    """Represents a response from ASK71 API"""
    
    def __init__(self, message: str, conversation_id: str, message_id: str):
        self.message = message
        self.conversation_id = conversation_id
        self.message_id = message_id
    
    def __repr__(self):
        return f"ASK71Response(conversation_id={self.conversation_id}, message_id={self.message_id})"


class ASK71Client:
    """Async client for interacting with ASK71 API with streaming support"""
    
    def __init__(self, api_key: str, agent_id: str, api_url: str):
        self.api_key = api_key
        self.agent_id = agent_id
        self.api_url = api_url
        self.client = httpx.AsyncClient(
            headers={
                "x-api-key": api_key,
                "Content-Type": "application/json"
            },
            timeout=httpx.Timeout(600.0)
        )
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
    
    async def stream_events(
        self,
        json_data: Dict[str, Any],
        timeout: Optional[int] = 6000,
        path: Optional[str] = "",
    ) -> AsyncGenerator[Tuple[str, str], None]:
        """
        Stream Server-Sent Events from the ASK71 API.
        
        Args:
            json_data: JSON payload for the request
            timeout: Request timeout in seconds
        
        Yields:
            Tuple[str, str]: Event type and data strings
        
        Raises:
            httpx.HTTPStatusError: If upstream service fails
        """
        
        request_kwargs = {
            "method": "POST",
            "url": f"{self.api_url.rstrip('/')}/{path.lstrip('/')}",
            "json": json_data,
            "headers": self.client.headers,
        }
        
        if timeout:
            request_kwargs["timeout"] = timeout
        
        async with aconnect_sse(self.client, **request_kwargs) as event_source:
            logger.info(
                f"Event stream started status_code: {event_source.response.status_code} "
                f"url: {str(event_source.response.url)}"
            )
            event_source.response.raise_for_status()
            
            async for sse_event in event_source.aiter_sse():
                yield sse_event.event, sse_event.data
            
    
    async def send_query(
        self, 
        query: str, 
        conversation_id: Optional[str] = None
    ) -> ASK71Response:
        """
        Send a query to ASK71 and get the aggregated streaming response
        
        Args:
            query: User's question or message
            conversation_id: Optional conversation ID to continue existing conversation
        
        Returns:
            ASK71Response object containing the response message and metadata
        
        Raises:
            httpx.HTTPStatusError: If the request fails
            ValueError: If the response format is invalid
        """
        payload = {
            "agent_id": self.agent_id,
            "query": query,
            "stream": True,
            "is_incognito": False
        }
        
        if conversation_id:
            payload["conversation_id"] = conversation_id
        
        logger.info(f"Sending query to ASK71: {query[:50]}...")
        
        try:
            # Collect and aggregate stream events
            complete_response = {}
            message = []
            
            async for event, data in self.stream_events(payload, path="/v1/conversations/"):
                if event == "error":
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=json.loads(data))
                if event in ("metadata", "conversation_created"):
                    complete_response.update(json.loads(data))
                    continue
                
                if event == "message":
                    message.append(json.loads(data).get("data", ""))
            
            # Aggregate message chunks
            complete_response["message"] = "".join(message)
            
            # Validate response structure
            if not isinstance(complete_response, dict):
                raise ValueError(f"Invalid response format: expected dict, got {type(complete_response)}")
            
            message_text = complete_response.get('message')
            conv_id = complete_response.get('conversation_id') or conversation_id
            msg_id = complete_response.get('message_id')
            
            logger.info(f"Received response from ASK71: conversation_id={conv_id}, message_id={msg_id}")
            
            return ASK71Response(
                message=message_text,
                conversation_id=conv_id,
                message_id=msg_id
            )
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Error sending query to ASK71: {e}")
            raise
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Error parsing ASK71 response: {e}")
            raise

