"""Aliyun Coding Plan (DashScope) ModelClient integration.

This client uses Anthropic API format for Alibaba Cloud DashScope Coding Plan endpoint.
"""

import os
import json
from typing import Dict, Optional, Any, AsyncGenerator
import logging

import aiohttp
from adalflow.core.model_client import ModelClient
from adalflow.core.types import ModelType, GeneratorOutput, CompletionUsage

from api.logging_config import setup_logging

setup_logging()
log = logging.getLogger(__name__)


class AliyunCodingClient(ModelClient):
    """A component wrapper for the Aliyun Coding Plan API client.

    Aliyun Coding Plan uses Anthropic API format through DashScope.

    Args:
        api_key (Optional[str], optional): Dashscope API key. Defaults to None.
        base_url (str): The API base URL. Defaults to "https://coding.dashscope.aliyuncs.com/apps/anthropic/v1".
        env_api_key_name (str): Environment variable name for the API key. Defaults to "DASHSCOPE_API_KEY".

    References:
        - Dashscope API Documentation: https://help.aliyun.com/zh/dashscope/
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        env_api_key_name: str = "DASHSCOPE_API_KEY",
    ):
        super().__init__()
        self._api_key = api_key
        self._env_api_key_name = env_api_key_name
        self.base_url = base_url or os.getenv(
            "ALIYUN_CODING_BASE_URL",
            "https://coding.dashscope.aliyuncs.com/apps/anthropic/v1"
        )
        self.api_key = self._api_key or os.getenv(self._env_api_key_name)

        if not self.api_key:
            raise ValueError(
                f"Environment variable {self._env_api_key_name} must be set"
            )

    def _get_headers(self) -> Dict[str, str]:
        """Get the headers for API requests.

        Aliyun Coding Plan requires both x-api-key and Authorization: Bearer headers.
        """
        return {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "Authorization": f"Bearer {self.api_key}",
            "anthropic-version": "2023-06-01",
            "User-Agent": "deepwiki/0.1.0",
        }

    def _prepare_messages(self, input: Any) -> list:
        """Prepare messages for the Anthropic API format."""
        if isinstance(input, str):
            return [{"role": "user", "content": input}]
        elif isinstance(input, list):
            return input
        else:
            raise ValueError(f"Unsupported input type: {type(input)}")

    def parse_chat_completion(self, response_data: Dict) -> GeneratorOutput:
        """Parse the Anthropic-format response to GeneratorOutput."""
        try:
            # Extract text from content array
            text_parts = []
            for item in response_data.get("content", []):
                if item.get("type") == "text":
                    text_parts.append(item.get("text", ""))

            full_text = "".join(text_parts)

            # Extract usage
            usage_data = response_data.get("usage", {})
            usage = CompletionUsage(
                prompt_tokens=usage_data.get("input_tokens", 0),
                completion_tokens=usage_data.get("output_tokens", 0),
                total_tokens=usage_data.get("input_tokens", 0) + usage_data.get("output_tokens", 0),
            )

            return GeneratorOutput(
                data=full_text,
                usage=usage,
                raw_response=json.dumps(response_data),
            )
        except Exception as e:
            log.error(f"Error parsing response: {e}")
            return GeneratorOutput(
                data=str(response_data),
                error=str(e),
                raw_response=json.dumps(response_data),
            )

    def convert_inputs_to_api_kwargs(
        self,
        input: Optional[Any] = None,
        model_kwargs: Dict = {},
        model_type: ModelType = ModelType.UNDEFINED,
    ) -> Dict:
        """Convert inputs to API kwargs for Anthropic format."""
        if model_type != ModelType.LLM:
            raise ValueError(f"model_type {model_type} is not supported by AliyunCodingClient")

        messages = self._prepare_messages(input)

        # Anthropic format requires max_tokens
        final_kwargs = {
            "model": model_kwargs.get("model", "kimi-k2.5"),
            "messages": messages,
            "max_tokens": model_kwargs.get("max_tokens", 4096),
            "stream": model_kwargs.get("stream", False),
        }

        # Add optional parameters
        if "temperature" in model_kwargs:
            final_kwargs["temperature"] = model_kwargs["temperature"]
        if "top_p" in model_kwargs:
            final_kwargs["top_p"] = model_kwargs["top_p"]
        if "top_k" in model_kwargs:
            final_kwargs["top_k"] = model_kwargs["top_k"]

        return final_kwargs

    async def acall(
        self, api_kwargs: Dict = {}, model_type: ModelType = ModelType.UNDEFINED
    ) -> Any:
        """Async call to the Aliyun Coding Plan API."""
        if model_type != ModelType.LLM:
            raise ValueError(f"model_type {model_type} is not supported")

        url = f"{self.base_url.rstrip('/')}/messages"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    headers=self._get_headers(),
                    json=api_kwargs,
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        log.error(f"API error {response.status}: {error_text}")
                        raise Exception(f"API error {response.status}: {error_text}")

                    if api_kwargs.get("stream", False):
                        # For streaming, read all content before session closes
                        chunks = []
                        line_count = 0
                        async for line in response.content:
                            line = line.decode('utf-8').strip()
                            line_count += 1
                            log.debug(f"SSE line {line_count}: {line[:200]}")
                            if line.startswith('data: '):
                                data = line[6:]  # Remove 'data: ' prefix
                                if data == '[DONE]':
                                    log.info("Received [DONE] marker")
                                    break
                                try:
                                    chunk = json.loads(data)
                                    log.debug(f"Parsed chunk: {chunk}")
                                    # Extract content from Anthropic format
                                    if chunk.get('type') == 'content_block_delta':
                                        delta = chunk.get('delta', {})
                                        if delta.get('type') == 'text':
                                            text = delta.get('text', '')
                                            if text:
                                                chunks.append(text)
                                                log.debug(f"Extracted text delta: {text[:100]}")
                                    elif chunk.get('type') == 'message':
                                        content = chunk.get('content', [])
                                        for item in content:
                                            if item.get('type') == 'text':
                                                text = item.get('text', '')
                                                if text:
                                                    chunks.append(text)
                                                    log.debug(f"Extracted message text: {text[:100]}")
                                    elif chunk.get('type') == 'message_start':
                                        log.debug("Received message_start")
                                    elif chunk.get('type') == 'message_delta':
                                        log.debug(f"Received message_delta: {chunk}")
                                    elif chunk.get('type') == 'message_stop':
                                        log.debug("Received message_stop")
                                    else:
                                        log.debug(f"Unknown chunk type: {chunk.get('type')}")
                                except json.JSONDecodeError as e:
                                    log.warning(f"Failed to decode SSE data: {data}, error: {e}")
                                    continue
                        log.info(f"Total SSE lines processed: {line_count}, chunks collected: {len(chunks)}")
                        if not chunks:
                            log.warning("No chunks collected from streaming response")
                        # Return an async generator that yields the collected chunks
                        async def _yield_chunks():
                            for chunk in chunks:
                                yield chunk
                        return _yield_chunks()
                    else:
                        response_data = await response.json()
                        return self.parse_chat_completion(response_data)

        except Exception as e:
            log.error(f"Error calling Aliyun Coding API: {e}")
            raise

    def call(self, api_kwargs: Dict = {}, model_type: ModelType = ModelType.UNDEFINED) -> Any:
        """Sync call to the Aliyun Coding Plan API."""
        import asyncio
        return asyncio.run(self.acall(api_kwargs, model_type))

    async def _handle_streaming_response(self, response) -> AsyncGenerator[str, None]:
        """Handle streaming response from the API."""
        try:
            # Read SSE stream line by line
            async for line in response.content:
                line = line.decode('utf-8').strip()
                if line.startswith('data: '):
                    data = line[6:]  # Remove 'data: ' prefix
                    if data == '[DONE]':
                        break
                    try:
                        chunk = json.loads(data)
                        # Extract content from Anthropic format
                        if chunk.get('type') == 'content_block_delta':
                            delta = chunk.get('delta', {})
                            if delta.get('type') == 'text':
                                text = delta.get('text', '')
                                if text:
                                    yield text
                        elif chunk.get('type') == 'message':
                            content = chunk.get('content', [])
                            for item in content:
                                if item.get('type') == 'text':
                                    text = item.get('text', '')
                                    if text:
                                        yield text
                    except json.JSONDecodeError:
                        log.warning(f"Failed to decode SSE data: {data}")
                        continue
        except Exception as e:
            log.error(f"Error handling streaming response: {e}")
            raise

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Create an instance from a dictionary."""
        return cls(**data)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "api_key": self._api_key,
            "base_url": self.base_url,
        }
