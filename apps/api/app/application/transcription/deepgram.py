"""
Deepgram Transcription Provider.

Isolated implementation — all Deepgram-specific code lives here.
CRM code never imports this directly.
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


class DeepgramProvider(TranscriptProvider):
    """Deepgram real-time speech-to-text provider.

    Uses Deepgram's WebSocket streaming API for live transcription
    with speaker diarization, punctuation, and confidence scores.

    In production, this uses the deepgram-sdk Python package.
    Currently provides the full interface with stub implementations.
    """

    def __init__(self, config: dict[str, Any]) -> None:
        self._api_key = config.get("api_key", "")
        self._model = config.get("model", "nova-2")
        self._language = config.get("language", "en")
        self._diarize = config.get("diarize", True)
        self._punctuate = config.get("punctuate", True)
        self._interim_results = config.get("interim_results", True)
        self._connected = False
        self._streaming = False
        self._on_event: TranscriptCallback | None = None
        self._sent_chunks = 0
        self._received_msgs = 0

    @property
    def provider_name(self) -> str:
        return "deepgram"

    async def connect(self, config: dict[str, Any]) -> bool:
        self._api_key = config.get("api_key", self._api_key)
        self._model = config.get("model", self._model)

        if not self._api_key:
            logger.error("Deepgram: missing API key")
            return False

        # In production: self._client = DeepgramClient(self._api_key)
        self._connected = True
        logger.info("Deepgram provider connected (model: %s)", self._model)
        return True

    async def disconnect(self) -> None:
        self._connected = False
        self._streaming = False
        self._on_event = None
        logger.info("Deepgram provider disconnected")

    async def start_streaming(self, on_event: TranscriptCallback) -> None:
        if not self._connected:
            await on_event(TranscriptEvent(
                type=TranscriptEventType.ERROR,
                error="Provider not connected",
            ))
            return

        self._on_event = on_event
        self._streaming = True

        await on_event(TranscriptEvent(type=TranscriptEventType.CONNECTED))
        logger.info("Deepgram streaming started")

    async def stop_streaming(self) -> None:
        self._streaming = False
        if self._on_event:
            await self._on_event(TranscriptEvent(type=TranscriptEventType.DISCONNECTED))
        self._on_event = None

    async def pause(self) -> None:
        self._streaming = False
        logger.info("Deepgram streaming paused")

    async def resume(self) -> None:
        self._streaming = True
        logger.info("Deepgram streaming resumed")

    async def send_audio(self, audio_bytes: bytes) -> None:
        """Send raw audio bytes to Deepgram via WebSocket streaming API."""
        if not self._connected or not self._streaming:
            return
        if not hasattr(self, "_ws") or self._ws is None:
            await self._connect_deepgram()
            if self._ws is None:
                return
        try:
            await self._ws.send_bytes(audio_bytes)
            self._sent_chunks += 1
            if self._sent_chunks % 50 == 0:
                logger.info("Deepgram: sent %d audio chunks (%d bytes each)", self._sent_chunks, len(audio_bytes))
        except Exception as e:
            logger.warning("Deepgram send error: %s", e)
            self._ws = None

    async def _connect_deepgram(self) -> None:
        """Connect to Deepgram using aiohttp WebSocket."""
        import aiohttp
        import asyncio
        url = (
            f"wss://api.deepgram.com/v1/listen"
            f"?model={self._model}"
            f"&language={self._language}"
            f"&encoding=linear16"
            f"&sample_rate=16000"
            f"&channels=1"
        )
        if self._diarize:
            url += "&diarize=true&diarize_version=2"
        if self._punctuate:
            url += "&punctuate=true"
        if self._interim_results:
            url += "&interim_results=true"
        try:
            session = aiohttp.ClientSession()
            self._ws = await session.ws_connect(
                url,
                headers={"Authorization": f"Token {self._api_key}"},
            )
            self._aiohttp_session = session
            asyncio.create_task(self._read_deepgram())
            logger.info("Deepgram WebSocket connected via aiohttp")
        except Exception as e:
            logger.warning("Deepgram connection failed: %s", e)
            self._ws = None

    async def _read_deepgram(self) -> None:
        """Read messages from Deepgram aiohttp WebSocket."""
        import aiohttp
        import json as _json
        try:
            async for msg in self._ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    self._received_msgs += 1
                    try:
                        data = _json.loads(msg.data)
                        msg_type = data.get("type", "?")
                        if self._received_msgs <= 3 or msg_type == "Results":
                            logger.info("Deepgram msg #%d type=%s text=%s",
                                self._received_msgs, msg_type,
                                str(data.get("channel", {}).get("alternatives", [{}])[0].get("transcript", ""))[:80] if msg_type == "Results" else "")
                        await self._handle_message(data)
                    except Exception as e:
                        logger.warning("Deepgram msg parse error: %s", e)
                elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                    logger.info("Deepgram WS closed/error: %s", msg.type)
                    break
        except Exception as e:
            logger.warning("Deepgram read error: %s", e)
        finally:
            logger.info("Deepgram: sent=%d chunks, received=%d msgs total", self._sent_chunks, self._received_msgs)
            self._ws = None
            if hasattr(self, "_aiohttp_session"):
                await self._aiohttp_session.close()

    async def _handle_message(self, data: dict) -> None:
        """Handle a parsed Deepgram message."""
        if data.get("type") == "Results":
            channel = data.get("channel", {})
            alternatives = channel.get("alternatives", [])
            if alternatives:
                alt = alternatives[0]
                text = alt.get("transcript", "")
                is_final = data.get("is_final", False)
                if text.strip() and self._on_event:
                    words_data = alt.get("words", [])
                    # Determine speaker from words array (Deepgram diarization)
                    speaker_counts: dict[str, int] = {}
                    for w in words_data:
                        spk = str(w.get("speaker", 0))
                        speaker_counts[spk] = speaker_counts.get(spk, 0) + 1
                    dominant_speaker = max(speaker_counts, key=speaker_counts.get) if speaker_counts else "0"
                    speaker_label = f"Speaker {dominant_speaker}"

                    words = [
                        TranscriptWord(
                            word=w.get("word", ""),
                            start=w.get("start", 0.0),
                            end=w.get("end", 0.0),
                            confidence=w.get("confidence", 0.0),
                            speaker=str(w.get("speaker", 0)) if w.get("speaker") is not None else None,
                        )
                        for w in words_data
                    ]
                    segment = TranscriptSegment(
                        id=f"dg-{hash(text) & 0xFFFF:04x}",
                        speaker=speaker_label,
                        text=text.strip(),
                        start=data.get("start", 0.0),
                        end=data.get("start", 0.0) + data.get("duration", 0.0),
                        confidence=alt.get("confidence", 0.0),
                        is_final=is_final,
                        words=words if is_final else [],
                    )
                    await self._on_event(TranscriptEvent(
                        type=TranscriptEventType.FINAL if is_final else TranscriptEventType.PARTIAL,
                        segment=segment,
                    ))

    async def get_supported_languages(self) -> list[str]:
        return ["en", "es", "fr", "de", "pt", "ja", "ko", "zh"]

    async def health_check(self) -> bool:
        return self._connected

    # ── Internal: simulate a transcript for testing ──

    async def _simulate_transcript(self, text: str, speaker: str = "Speaker 0") -> None:
        """For testing: emit a simulated final transcript segment."""
        if not self._on_event:
            return

        segment = TranscriptSegment(
            id=f"sim_{hash(text) & 0xFFFF:04x}",
            speaker=speaker,
            text=text,
            start=0.0,
            end=1.0,
            confidence=0.95,
            is_final=True,
            words=[TranscriptWord(word=w, start=0.0, end=0.5, confidence=0.95) for w in text.split()],
            language=self._language,
        )
        await self._on_event(TranscriptEvent(
            type=TranscriptEventType.FINAL,
            segment=segment,
        ))
