"""KittenTTS Service Provider for Hermes Agent."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from agent.tts_provider import TTSProvider, DEFAULT_OUTPUT_FORMAT
try:
    from .client import KittenTTSClient, DEFAULT_BASE_URL, DEFAULT_MODELS, DEFAULT_VOICES
except (ImportError, ValueError):
    from client import KittenTTSClient, DEFAULT_BASE_URL, DEFAULT_MODELS, DEFAULT_VOICES

logger = logging.getLogger("plugins.kittentts_service")


class KittenTTSServiceProvider(TTSProvider):
    """First-class TTS Provider integrating Hermes with the local KittenTTS CPU service."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.base_url = str(self.config.get("base_url") or DEFAULT_BASE_URL)
        self.timeout_seconds = float(self.config.get("timeout_seconds") or 30.0)
        self.client = KittenTTSClient(self.base_url, self.timeout_seconds)

    @property
    def name(self) -> str:
        return "kittentts-service"

    @property
    def display_name(self) -> str:
        return "KittenTTS Service (Local CPU)"

    def is_available(self) -> bool:
        """Check if local KittenTTS background service is online or Anaconda environment exists."""
        if self.client.is_healthy():
            return True
        conda_py = Path(r"E:\Anaconda\envs\kittentts2\python.exe")
        return conda_py.is_file()

    def list_voices(self) -> List[Dict[str, Any]]:
        """Return structured voice rows for Hermes settings."""
        voices = self.client.get_voices()
        return [{"id": v, "display": v, "language": "en"} for v in voices]

    def default_voice(self) -> Optional[str]:
        return str(self.config.get("voice") or "Kiki")

    def list_models(self) -> List[Dict[str, Any]]:
        """Return structured model rows for Hermes settings."""
        models = self.client.get_models()
        return [{"id": m, "display": m.split("/")[-1]} for m in models]

    def default_model(self) -> Optional[str]:
        return str(self.config.get("model") or "KittenML/kitten-tts-mini-0.8")

    def synthesize(
        self,
        text: str,
        output_path: str,
        *,
        voice: Optional[str] = None,
        model: Optional[str] = None,
        speed: Optional[float] = None,
        format: str = DEFAULT_OUTPUT_FORMAT,
        **extra: Any,
    ) -> str:
        """Synthesize speech using the persistent local KittenTTS service."""
        target_voice = voice or self.default_voice() or "Kiki"
        target_model = model or self.default_model() or "KittenML/kitten-tts-mini-0.8"
        target_speed = float(speed) if speed is not None else float(self.config.get("speed", 1.0))

        logger.info(
            "[KittenTTS Service Plugin] Synthesizing with model=%s, voice=%s, speed=%.2f",
            target_model,
            target_voice,
            target_speed,
        )

        return self.client.synthesize(
            text=text,
            output_path=output_path,
            voice=target_voice,
            model=target_model,
            speed=target_speed,
            response_format=format or "wav",
        )
