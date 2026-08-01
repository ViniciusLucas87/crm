"""
OpenAI Whisper Transcription Provider.

Uses OpenAI's real-time API for streaming speech-to-text.
""" 
import logging
from typing import Any

from app.application.transcription import (
    TranscriptCallback,
    TranscriptEvent,
    TranscriptEventType,
    TranscriptProvider,
    TranscriptSegment,
    TranscriptWord,
)

logger = logging.getLogger(__name__)


class OpenAIWhisperProvider(TranscriptProvider):
    """OpenAI Whisper real-time speech-to-text provider.

    Uses OpenAI's Realtime API for streaming transcription.
    """

    def __init__(self, config: dict[str, Any]) -> None:
        self._api_key = config.get("api_key", "")
        self._model = config.get("model", "whisper-1")
        self._language = config.get("language", "en")
        self._connected = False
        self._streaming = False
        self._on_event: TranscriptCallback | None = None

    @property
    def provider_name(self) -> str:
        return "openai"

    async def connect(self, config: dict[str, Any]) -> bool:
        self._api_key = config.get("api_key", self._api_key)
        if not self._api_key:
            logger.error("OpenAI Whisper: missing API key")
            return False
        self._connected = True
        logger.info("OpenAI Whisper provider connected")
        return True

    async def disconnect(self) -> None:
        self._connected = False
        self._streaming = False
        self._on_event = None
        logger.info("OpenAI Whisper provider disconnected")

    async def start_streaming(self, on_event: TranscriptCallback) -> None:
        if not self._connected:
            await on_event(TranscriptEvent(type=TranscriptEventType.ERROR, error="Provider not connected"))
            return
        self._on_event = on_event
        self._streaming = True
        await on_event(TranscriptEvent(type=TranscriptEventType.CONNECTED))
        logger.info("OpenAI Whisper streaming started")

    async def stop_streaming(self) -> None:
        self._streaming = False
        if self._on_event:
            await self._on_event(TranscriptEvent(type=TranscriptEventType.DISCONNECTED))
        self._on_event = None

    async def send_audio(self, audio_bytes: bytes) -> None:
        """Buffer audio and periodically transcribe via OpenAI Whisper REST API."""
        if not self._connected or not self._on_event:
            return
        # Accumulate audio in buffer
        if not hasattr(self, "_audio_buffer"):
            self._audio_buffer = bytearray()
            self._buffer_count = 0
        self._audio_buffer.extend(audio_bytes)
        self._buffer_count += 1
        # Every ~50 chunks (~2.5s at 20ms frames), send to Whisper
        if self._buffer_count >= 50:
            await self._transcribe_buffer()

    async def _transcribe_buffer(self) -> None:
        """Send buffered audio to OpenAI Whisper API."""
        import base64
        import httpx
        if not hasattr(self, "_audio_buffer") or len(self._audio_buffer) < 1600:
            return
        audio_b64 = base64.b64encode(bytes(self._audio_buffer)).decode()
        self._audio_buffer = bytearray()
        self._buffer_count = 0
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.post(
                    "https://api.openai.com/v1/audio/transcriptions",
                    headers={"Authorization": f"Bearer {self._api_key}"},
                    data={"model": self._model, "language": self._language, "response_format": "json"},
                    files={"file": ("audio.webm", bytes(self._audio_buffer) or audio_b64.encode(), "audio/webm")},
                )
            if r.status_code == 200 and self._on_event:
                text = r.json().get("text", "")
                if text.strip():
                    await self._on_event(TranscriptEvent(
                        type=TranscriptEventType.PARTIAL,
                        text=text.strip(),
                        is_final=False,
                        confidence=0.8,
                    ))
            else:
                logger.warning("OpenAI Whisper API error: %s %s", r.status_code, r.text[:200])
        except Exception as e:
            logger.warning("OpenAI Whisper HTTP error: %s", e)

    async def get_supported_languages(self) -> list[str]:
        return ["en", "es", "fr", "de", "it", "pt", "nl", "ja", "ko", "zh", "ar", "ru", "tr", "pl", "uk", "vi", "ca", "sv", "hi", "fi"]

    async def health_check(self) -> bool:
        return self._connected
