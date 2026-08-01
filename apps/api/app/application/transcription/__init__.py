"""
Transcript Provider — abstract interface for real-time speech-to-text.

Every transcription provider (Deepgram, AssemblyAI, OpenAI, Azure, Google)
implements this interface. Follows the same provider pattern as CallProvider
and IntelligenceProvider.

Architecture:
    Communication Channel → TranscriptProvider → StreamingEngine → ConversationIntelligence
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Callable, Awaitable


class TranscriptEventType(StrEnum):
    PARTIAL = "partial"
    FINAL = "final"
    SPEAKER_CHANGE = "speaker_change"
    ERROR = "error"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"


@dataclass
class TranscriptWord:
    word: str
    start: float
    end: float
    confidence: float = 1.0
    speaker: str | None = None


@dataclass
class TranscriptSegment:
    """A single transcript segment (one utterance)."""
    id: str = ""
    speaker: str = "Speaker 0"
    text: str = ""
    start: float = 0.0
    end: float = 0.0
    confidence: float = 0.0
    is_final: bool = False
    words: list[TranscriptWord] = field(default_factory=list)
    language: str | None = None


@dataclass
class TranscriptEvent:
    """Event emitted during live transcription."""
    type: TranscriptEventType
    segment: TranscriptSegment | None = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


# Callback type
TranscriptCallback = Callable[[TranscriptEvent], Awaitable[None]]


class TranscriptProvider(ABC):
    """Abstract interface for all Transcription Providers.

    Usage:
        class DeepgramProvider(TranscriptProvider):
            @property
            def provider_name(self) -> str: return "deepgram"

            async def connect(self, config: dict) -> bool: ...
            async def start_streaming(self, audio_source) -> None: ...
    """

    def __init__(self) -> None:
        self._reconnect_attempts = 0
        self._max_reconnect_attempts = 3
        self._reconnect_delay = 2.0  # seconds

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Unique identifier: 'deepgram', 'assemblyai', 'openai', etc."""
        ...

    @abstractmethod
    async def connect(self, config: dict[str, Any]) -> bool:
        """Initialize connection to the transcription service."""
        ...

    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection and clean up resources."""
        ...

    @abstractmethod
    async def start_streaming(self, on_event: TranscriptCallback) -> None:
        """Begin streaming audio for transcription. Calls on_event for each result."""
        ...

    @abstractmethod
    async def stop_streaming(self) -> None:
        """Stop streaming and finalize any pending transcripts."""
        ...

    async def send_audio(self, audio_bytes: bytes) -> None:
        """Send raw audio bytes to the provider for transcription.
        
        Default: no-op. Providers with native streaming (Deepgram) override this.
        REST-based providers (OpenAI) use a buffered approach.
        """
        pass

    async def pause(self) -> None:
        """Pause transcription (default: no-op)."""
        pass

    async def resume(self) -> None:
        """Resume transcription (default: no-op)."""
        pass

    async def get_supported_languages(self) -> list[str]:
        """Return list of supported language codes."""
        return ["en"]

    async def health_check(self) -> bool:
        """Verify provider connectivity."""
        return True

    async def reconnect(self, config: dict[str, Any], on_event: TranscriptCallback) -> bool:
        """Attempt reconnection with exponential backoff."""
        import asyncio

        if self._reconnect_attempts >= self._max_reconnect_attempts:
            await on_event(TranscriptEvent(
                type=TranscriptEventType.ERROR,
                error=f"Max reconnect attempts ({self._max_reconnect_attempts}) reached",
            ))
            return False

        self._reconnect_attempts += 1
        delay = self._reconnect_delay * (2 ** (self._reconnect_attempts - 1))
        await asyncio.sleep(delay)

        try:
            connected = await self.connect(config)
            if connected:
                self._reconnect_attempts = 0
                await self.start_streaming(on_event)
                return True
        except Exception:
            pass

        return False


def create_transcript_provider(name: str, config: dict[str, Any] | None = None) -> TranscriptProvider:
    """Factory: create a TranscriptProvider by name."""
    cfg = config or {}
    if name == "deepgram":
        from app.application.transcription.deepgram import DeepgramProvider
        return DeepgramProvider(cfg)
    if name == "openai":
        from app.application.transcription.openai import OpenAIWhisperProvider
        return OpenAIWhisperProvider(cfg)
    if name == "assemblyai":
        from app.application.transcription.assemblyai import AssemblyAIProvider
        return AssemblyAIProvider(cfg)
    if name == "gladia":
        from app.application.transcription.gladia import GladiaProvider
        return GladiaProvider(cfg)
    if name == "mock":
        return MockTranscriptProvider()
    raise ValueError(f"Unknown transcript provider: {name}")


class MockTranscriptProvider(TranscriptProvider):
    """Simulated transcription provider for development/testing."""

    def __init__(self) -> None:
        self._connected = False

    @property
    def provider_name(self) -> str:
        return "mock"

    async def connect(self, config: dict[str, Any]) -> bool:
        self._connected = True
        return True

    async def disconnect(self) -> None:
        self._connected = False

    async def start_streaming(self, on_event: TranscriptCallback) -> None:
        pass

    async def stop_streaming(self) -> None:
        pass
