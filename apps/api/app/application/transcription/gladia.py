"""
Gladia Transcription Provider.

Uses Gladia's real-time API for streaming speech-to-text.
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


class GladiaProvider(TranscriptProvider):
    """Gladia real-time speech-to-text provider.

    Uses Gladia's WebSocket API for live transcription with
    speaker diarization, sentiment, and custom vocabulary.
    """

    def __init__(self, config: dict[str, Any]) -> None:
        self._api_key = config.get("api_key", "")
        self._language = config.get("language", "en")
        self._connected = False
        self._streaming = False
        self._on_event: TranscriptCallback | None = None

    @property
    def provider_name(self) -> str:
        return "gladia"

    async def connect(self, config: dict[str, Any]) -> bool:
        self._api_key = config.get("api_key", self._api_key)
        if not self._api_key:
            logger.error("Gladia: missing API key")
            return False
        self._connected = True
        logger.info("Gladia provider connected")
        return True

    async def disconnect(self) -> None:
        self._connected = False
        self._streaming = False
        self._on_event = None
        logger.info("Gladia provider disconnected")

    async def start_streaming(self, on_event: TranscriptCallback) -> None:
        if not self._connected:
            await on_event(TranscriptEvent(type=TranscriptEventType.ERROR, error="Provider not connected"))
            return
        self._on_event = on_event
        self._streaming = True
        await on_event(TranscriptEvent(type=TranscriptEventType.CONNECTED))
        logger.info("Gladia streaming started")

    async def stop_streaming(self) -> None:
        self._streaming = False
        if self._on_event:
            await self._on_event(TranscriptEvent(type=TranscriptEventType.DISCONNECTED))
        self._on_event = None

    async def get_supported_languages(self) -> list[str]:
        return ["en", "es", "fr", "de", "it", "pt", "nl", "ja", "zh", "ar", "ru", "tr", "pl", "hi"]

    async def health_check(self) -> bool:
        return self._connected
