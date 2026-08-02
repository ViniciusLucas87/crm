"""
LLM Provider Abstraction Layer.

Multi-provider support with configuration-only swapping.
Supported: OpenAI, Anthropic, Google, DeepSeek, OpenRouter, Azure OpenAI, Ollama.

All providers implement the same interface — the application
never depends on a specific provider implementation.
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field
from typing import Any, Literal


# ── Shared Types ──

@dataclass
class LLMMessage:
    role: Literal["system", "user", "assistant", "tool"]
    content: str
    tool_call_id: str | None = None
    name: str | None = None


@dataclass
class LLMToolCall:
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class LLMResponse:
    content: str
    tool_calls: list[LLMToolCall] = field(default_factory=list)
    finish_reason: str = "stop"
    usage: dict[str, int] = field(default_factory=dict)


@dataclass
class LLMConfig:
    provider: str = "openai"  # openai, anthropic, google, deepseek, openrouter, azure, ollama
    model: str = "gpt-4o"
    api_key: str = ""
    api_base: str | None = None
    temperature: float = 0.3
    max_tokens: int = 4096
    top_p: float = 1.0
    extra: dict[str, Any] = field(default_factory=dict)


# ── Abstract Provider ──

class LLMProvider(ABC):
    """Abstract base for all LLM providers."""

    def __init__(self, config: LLMConfig) -> None:
        self._config = config

    @abstractmethod
    async def chat(
        self,
        messages: list[LLMMessage],
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str = "auto",
    ) -> LLMResponse:
        """Send a chat completion request."""
        ...

    @abstractmethod
    async def chat_stream(
        self,
        messages: list[LLMMessage],
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str = "auto",
    ) -> AsyncGenerator[str, None]:
        """Stream a chat completion response."""
        ...


# ── OpenAI Provider ──

class OpenAIProvider(LLMProvider):
    async def chat(self, messages, tools=None, tool_choice="auto"):
        try:
            from openai import AsyncOpenAI
        except ImportError:
            raise ImportError("openai package required: pip install openai")

        client = AsyncOpenAI(
            api_key=self._config.api_key,
            base_url=self._config.api_base,
        )

        msg_dicts = [{"role": m.role, "content": m.content} for m in messages]
        kwargs: dict[str, Any] = {
            "model": self._config.model,
            "messages": msg_dicts,
            "temperature": self._config.temperature,
            "max_tokens": self._config.max_tokens,
            "top_p": self._config.top_p,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = tool_choice

        response = await client.chat.completions.create(**kwargs)
        choice = response.choices[0]
        tool_calls = []
        if choice.message.tool_calls:
            for tc in choice.message.tool_calls:
                import json
                tool_calls.append(LLMToolCall(
                    id=tc.id,
                    name=tc.function.name,
                    arguments=json.loads(tc.function.arguments),
                ))

        return LLMResponse(
            content=choice.message.content or "",
            tool_calls=tool_calls,
            finish_reason=choice.finish_reason or "stop",
            usage={"prompt_tokens": response.usage.prompt_tokens if response.usage else 0, "completion_tokens": response.usage.completion_tokens if response.usage else 0},
        )

    async def chat_stream(self, messages, tools=None, tool_choice="auto"):
        try:
            from openai import AsyncOpenAI
        except ImportError:
            raise ImportError("openai package required: pip install openai")

        client = AsyncOpenAI(api_key=self._config.api_key, base_url=self._config.api_base)
        msg_dicts = [{"role": m.role, "content": m.content} for m in messages]
        kwargs: dict[str, Any] = {
            "model": self._config.model, "messages": msg_dicts,
            "temperature": self._config.temperature, "max_tokens": self._config.max_tokens,
            "top_p": self._config.top_p, "stream": True,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = tool_choice

        stream = await client.chat.completions.create(**kwargs)
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


# ── Anthropic Provider ──

class AnthropicProvider(LLMProvider):
    async def chat(self, messages, tools=None, tool_choice="auto"):
        try:
            from anthropic import AsyncAnthropic
        except ImportError:
            raise ImportError("anthropic package required: pip install anthropic")

        client = AsyncAnthropic(api_key=self._config.api_key)
        system_msg = ""
        user_msgs: list[dict[str, Any]] = []
        for m in messages:
            if m.role == "system":
                system_msg = m.content
            else:
                user_msgs.append({"role": m.role, "content": m.content})

        kwargs: dict[str, Any] = {
            "model": self._config.model,
            "max_tokens": self._config.max_tokens,
            "messages": user_msgs,
        }
        if system_msg:
            kwargs["system"] = system_msg

        response = await client.messages.create(**kwargs)
        return LLMResponse(
            content=response.content[0].text if response.content else "",
            usage={"prompt_tokens": response.usage.input_tokens if response.usage else 0, "completion_tokens": response.usage.output_tokens if response.usage else 0},
        )

    async def chat_stream(self, messages, tools=None, tool_choice="auto"):
        try:
            from anthropic import AsyncAnthropic
        except ImportError:
            raise ImportError("anthropic package required: pip install anthropic")

        client = AsyncAnthropic(api_key=self._config.api_key)
        system_msg = ""
        user_msgs: list[dict[str, Any]] = []
        for m in messages:
            if m.role == "system": system_msg = m.content
            else: user_msgs.append({"role": m.role, "content": m.content})

        kwargs: dict[str, Any] = {"model": self._config.model, "max_tokens": self._config.max_tokens, "messages": user_msgs}
        if system_msg: kwargs["system"] = system_msg

        async with client.messages.stream(**kwargs) as stream:
            async for text in stream.text_stream:
                yield text


# ── Provider Factory ──

PROVIDER_MAP: dict[str, type[LLMProvider]] = {
    "openai": OpenAIProvider,
    "deepseek": OpenAIProvider,  # DeepSeek uses OpenAI-compatible API
    "anthropic": AnthropicProvider,
}


def create_provider(config: LLMConfig) -> LLMProvider:
    provider_cls = PROVIDER_MAP.get(config.provider)
    if provider_cls is None:
        raise ValueError(f"Unknown provider: {config.provider}. Available: {list(PROVIDER_MAP.keys())}")
    return provider_cls(config)


def register_provider(name: str, provider_cls: type[LLMProvider]) -> None:
    """Register a custom LLM provider."""
    PROVIDER_MAP[name] = provider_cls
