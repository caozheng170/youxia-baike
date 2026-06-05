"""Flipbook server configuration."""

import os
from pathlib import Path

# Load variables from a .env file at the project root (if present).
try:
    from dotenv import load_dotenv

    _ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(_ENV_PATH)
except ImportError:
    pass

# Model provider: "local", "cloud", or "mock"
MODEL_PROVIDER = os.getenv("MODEL_PROVIDER", "mock")

# ── Local model (Xinference, OpenAI-compatible) ──────────────────────────
# Base URL of the Xinference server (the "/v1/..." path is appended in code).
LOCAL_XINFERENCE_URL = os.getenv("LOCAL_XINFERENCE_URL", "http://localhost:9997")
LOCAL_API_KEY = os.getenv("LOCAL_API_KEY", "")
LOCAL_IMAGE_MODEL = os.getenv("LOCAL_IMAGE_MODEL", "Z-Image-Turbo")
LOCAL_VL_MODEL = os.getenv("LOCAL_VL_MODEL", "qwen3.6-1")
# Text LLM used to rewrite/enrich image prompts (qwen3.6-1 handles both text & vision).
LOCAL_LLM_MODEL = os.getenv("LOCAL_LLM_MODEL", "qwen3.6-1")

# ── Cloud model (OpenAI-compatible API, e.g. agnes apihub) ───────────────
# Base URL should already include the "/v1" suffix.
CLOUD_BASE_URL = os.getenv("CLOUD_BASE_URL", "https://apihub.agnes-ai.com/v1")
CLOUD_API_KEY = os.getenv("CLOUD_API_KEY", "")
CLOUD_IMAGE_MODEL = os.getenv("CLOUD_IMAGE_MODEL", "agnes-image-2.1-flash")
# Click understanding sends an image, so it must use a multimodal model.
# Agnes 2.0-flash is text-only; only 1.5-flash accepts image input.
CLOUD_VL_MODEL = os.getenv("CLOUD_VL_MODEL", "agnes-1.5-flash")
# Text LLM used to rewrite/enrich image prompts (agnes-2.0-flash is the strong text model).
CLOUD_TEXT_MODEL = os.getenv("CLOUD_TEXT_MODEL", "agnes-2.0-flash")

# Server settings
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# Storage
STORAGE_DIR = os.getenv("STORAGE_DIR", "./data/pages")

# Image defaults
DEFAULT_WIDTH = 1280
DEFAULT_HEIGHT = 720
PREVIEW_WIDTH = 640
PREVIEW_HEIGHT = 360
