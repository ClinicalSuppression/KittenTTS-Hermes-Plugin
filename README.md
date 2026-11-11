# KittenTTS-Hermes-Plugin

> Production-grade KittenTTS local CPU service plugin for **Hermes Agent** and **Hermes Desktop**.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Hermes Compatible](https://img.shields.io/badge/Hermes-Plugin-purple.svg)](https://github.com/NousResearch/hermes-agent)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-brightgreen.svg)](https://www.python.org/)

---

## Overview

**KittenTTS-Hermes-Plugin** connects Hermes Desktop and Hermes Agent directly to a high-speed, local **KittenTTS** speech synthesis service running strictly on **CPU** (zero GPU/VRAM footprint).

By keeping lightweight ONNX models (25–80 MB) warm in RAM inside a dedicated background service, speech synthesis is near-instantaneous and fully decoupled from Hermes's internal environments.

---

## Features

- ⚡ **Near-Instant Speech Synthesis:** Communicates with a local background HTTP service over `http://127.0.0.1:8100`, skipping cold-start disk reads on every response.
- 💻 **Strictly CPU-Only:** Zero GPU or VRAM usage—keeps your GPU 100% free for large language models, vision, and local inference.
- 🎙️ **8 English Voices:** Seamlessly switch between **Kiki**, **Bella**, **Rosie**, **Luna**, **Jasper**, **Bruno**, **Hugo**, and **Leo**.
- 📦 **Multi-Model Support:** Full dynamic support for:
  - `KittenML/kitten-tts-mini-0.8` (80 MB — **Best quality CPU**, default)
  - `KittenML/kitten-tts-micro-0.8` (41 MB — Balanced speed & quality)
  - `KittenML/kitten-tts-nano-0.8` (56 MB — Fast fp32 model)
  - `KittenML/kitten-tts-nano-0.8-int8` (25 MB — Ultra-compact int8 model)
- 🔌 **Official Plugin Architecture:** Lives entirely in user plugin space (`~/.hermes/plugins/` or `E:\Hermes\plugins\`), touching zero core Hermes application code.
- 🌐 **System-Wide Compatibility:** The underlying Anaconda service also exposes standard OpenAI `/v1/audio/speech` and `/v1/voices` endpoints for any other application on your machine.

---

## Quick Start

### 1. Installation

Clone or drop this plugin repository into your Hermes plugins directory:

```bash
# Windows
git clone https://github.com/ClinicalSuppression/KittenTTS-Hermes-Plugin.git E:/Hermes/plugins/kittentts-service

# Linux / macOS
git clone https://github.com/ClinicalSuppression/KittenTTS-Hermes-Plugin.git ~/.hermes/plugins/kittentts-service
```

### 2. Configure Hermes

Add or update your `config.yaml` (`~/.hermes/config.yaml` or `E:\Hermes\config.yaml`):

```yaml
tts:
  provider: kittentts-service
  kittentts-service:
    base_url: http://127.0.0.1:8100
    model: KittenML/kitten-tts-mini-0.8
    voice: Kiki
    speed: 1.0
    timeout_seconds: 30
```

### 3. Background Service Launcher

Ensure your KittenTTS service is running on `http://127.0.0.1:8100`. You can start it anytime with:

```bash
# Windows
start_kittentts_service.cmd

# Or via Python in your Anaconda environment
python E:\Anaconda\envs\kittentts2\Scripts\kittentts_server.py
```

---

## Configuration Settings

| Setting | Type | Default | Description |
| --- | --- | --- | --- |
| `base_url` | `string` | `http://127.0.0.1:8100` | HTTP URL of the local KittenTTS service |
| `model` | `select` | `KittenML/kitten-tts-mini-0.8` | Active ONNX model ID |
| `voice` | `select` | `Kiki` | Default voice (`Kiki`, `Bella`, `Rosie`, `Luna`, `Jasper`, `Bruno`, `Hugo`, `Leo`) |
| `speed` | `number` | `1.0` | Speech rate multiplier (0.5 – 2.0) |
| `timeout_seconds` | `number` | `30` | Request timeout deadline |

---

## API Endpoints (Local Service)

The background service running on `http://127.0.0.1:8100` exposes:

- `GET /health` — Service status & active models in memory.
- `GET /v1/models` — Lists available KittenTTS models.
- `GET /v1/voices` — Lists all 8 available voices.
- `POST /v1/audio/speech` — OpenAI-compatible speech synthesis endpoint.
- `POST /tts` — Simple JSON text synthesis endpoint.

---

## License

This project is licensed under the [MIT License](LICENSE) — free for personal, open-source, and commercial use.
