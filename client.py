"""HTTP client for communicating with the local KittenTTS background service."""

import json
import logging
import os
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("plugins.kittentts_service.client")

DEFAULT_BASE_URL = "http://127.0.0.1:8100"
DEFAULT_TIMEOUT_SECONDS = 30.0

DEFAULT_VOICES = ["Kiki", "Bella", "Rosie", "Luna", "Jasper", "Bruno", "Hugo", "Leo"]
DEFAULT_MODELS = [
    "KittenML/kitten-tts-mini-0.8",
    "KittenML/kitten-tts-micro-0.8",
    "KittenML/kitten-tts-nano-0.8",
    "KittenML/kitten-tts-nano-0.8-int8",
]


class KittenTTSClient:
    """Client for the local KittenTTS CPU service."""

    def __init__(self, base_url: str = DEFAULT_BASE_URL, timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS):
        self.base_url = (base_url or DEFAULT_BASE_URL).rstrip("/")
        self.timeout_seconds = float(timeout_seconds or DEFAULT_TIMEOUT_SECONDS)

    def is_healthy(self) -> bool:
        """Check if the KittenTTS HTTP service is running and responsive."""
        url = f"{self.base_url}/health"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Hermes-KittenTTS-Plugin"})
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    return data.get("status") == "ok"
        except Exception as exc:
            logger.debug("Health check failed at %s: %s", url, exc)
        return False

    def get_voices(self, model: Optional[str] = None) -> List[str]:
        """Fetch available voices dynamically from the local service."""
        url = f"{self.base_url}/v1/voices"
        if model:
            url += f"?model={urllib.parse.quote(model)}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Hermes-KittenTTS-Plugin"})
            with urllib.request.urlopen(req, timeout=4.0) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    voices = data.get("voices")
                    if isinstance(voices, list) and voices:
                        return [str(v) for v in voices]
        except Exception as exc:
            logger.debug("Failed to list voices from %s: %s", url, exc)
        return list(DEFAULT_VOICES)

    def get_models(self) -> List[str]:
        """Fetch available models dynamically from the local service."""
        url = f"{self.base_url}/v1/models"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Hermes-KittenTTS-Plugin"})
            with urllib.request.urlopen(req, timeout=4.0) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    models = [m.get("id") for m in data.get("data", []) if isinstance(m, dict) and "id" in m]
                    if models:
                        return models
        except Exception as exc:
            logger.debug("Failed to list models from %s: %s", url, exc)
        return list(DEFAULT_MODELS)

    def synthesize(
        self,
        text: str,
        output_path: str,
        *,
        voice: Optional[str] = None,
        model: Optional[str] = None,
        speed: Optional[float] = None,
        response_format: str = "wav",
    ) -> str:
        """Synthesize text into output_path using the background HTTP service."""
        url = f"{self.base_url}/v1/audio/speech"
        payload = {
            "input": text,
            "voice": voice or "Kiki",
            "model": model or "KittenML/kitten-tts-mini-0.8",
            "speed": float(speed) if speed is not None else 1.0,
            "response_format": response_format or "wav",
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Hermes-KittenTTS-Plugin/0.1.0",
            },
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
                if resp.status != 200:
                    raise RuntimeError(f"HTTP {resp.status}: {resp.read().decode('utf-8', errors='ignore')}")
                audio_bytes = resp.read()
        except urllib.error.HTTPError as http_err:
            body = http_err.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"KittenTTS service error (HTTP {http_err.code}): {body}") from http_err
        except Exception as exc:
            raise RuntimeError(f"Failed to communicate with KittenTTS service at {self.base_url}: {exc}") from exc

        out = Path(output_path).expanduser().resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(audio_bytes)

        if not out.is_file() or out.stat().st_size == 0:
            raise RuntimeError(f"KittenTTS output file is empty at {output_path}")

        return str(out)
