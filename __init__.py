"""KittenTTS Service Plugin for Hermes Agent and Hermes Desktop."""

from .provider import KittenTTSServiceProvider


def register(ctx):
    """Register the KittenTTS Service TTS provider with Hermes."""
    ctx.register_tts_provider(KittenTTSServiceProvider())
