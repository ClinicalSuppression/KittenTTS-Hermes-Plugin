"""KittenTTS Service Provider for Hermes Agent."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from agent.tts_provider import TTSProvider, DEFAULT_OUTPUT_FORMAT
try:
    from .client import KittenTTSClient, DEFAULT_BASE_URL, DEFAULT_MODELS, DEFAULT_VOICES
except (ImportError, ValueError):
    from client import KittenTTSClient, DEFAULT_BASE_URL, DEFAULT_MODELS, DEFAULT_VOICES

logger = logging.getLogger("plugins.kittentts_service")

FALLBACK_VOICE = "Kiki"
FALLBACK_MODEL = "KittenML/kitten-tts-mini-0.8"
KNOWN_VOICES = frozenset(DEFAULT_VOICES)
HERMES_CONFIG_PATH = Path(os.environ.get("HERMES_CONFIG_PATH", r"E:\Hermes\config.yaml"))


def _load_live_config() -> Dict[str, Any]:
    """Read Hermes config.yaml fresh on every call so voice/model edits apply without a restart."""
    try:
        import yaml  # Hermes' Python ships PyYAML
        with HERMES_CONFIG_PATH.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
        return data if isinstance(data, dict) else {}
    except Exception as exc:
        logger.warning("[KittenTTS Service Plugin] Could not read %s: %s", HERMES_CONFIG_PATH, exc)
        return {}


def _live_setting(key: str) -> Optional[str]:
    """Resolve a setting from config.yaml in priority order: tts section, then plugin settings."""
    cfg = _load_live_config()
    tts_val = (((cfg.get("tts") or {}).get("kittentts-service")) or {}).get(key)
    if tts_val:
        return str(tts_val)
    plugin_val = ((((cfg.get("plugins") or {}).get("entries") or {}).get("kittentts-service") or {})
                  .get("settings") or {}).get(key)
    if plugin_val:
        return str(plugin_val)
    return None


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
        voice = _live_setting("voice") or FALLBACK_VOICE
        if voice not in KNOWN_VOICES:
            logger.warning("[KittenTTS Service Plugin] Unknown voice %r in config; using %s", voice, FALLBACK_VOICE)
            return FALLBACK_VOICE
        return voice

    def list_models(self) -> List[Dict[str, Any]]:
        """Return structured model rows for Hermes settings."""
        models = self.client.get_models()
        return [{"id": m, "display": m.split("/")[-1]} for m in models]

    def default_model(self) -> Optional[str]:
        return _live_setting("model") or FALLBACK_MODEL

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
        target_voice = voice or self.default_voice() or FALLBACK_VOICE
        if target_voice not in KNOWN_VOICES:
            raise ValueError(f"Unknown KittenTTS voice {target_voice!r}; choose from {sorted(KNOWN_VOICES)}")
        target_model = model or self.default_model() or FALLBACK_MODEL
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
