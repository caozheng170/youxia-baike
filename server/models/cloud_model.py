"""Cloud image model using an OpenAI-compatible API (e.g. agnes apihub)."""

import base64
import httpx
from . import ImageModel
from ..config import CLOUD_BASE_URL, CLOUD_API_KEY, CLOUD_IMAGE_MODEL


def _supported_size(width: int, height: int) -> str:
    """Snap arbitrary dimensions to a size Agnes supports (1024x768 / 1024x1024 / 768x1024)."""
    if width > height:
        return "1024x768"
    if height > width:
        return "768x1024"
    return "1024x1024"


class CloudImageModel(ImageModel):
    """Generate images via an OpenAI-compatible cloud API (Agnes apihub)."""

    def __init__(self):
        self.base_url = CLOUD_BASE_URL.rstrip("/")
        self.api_key = CLOUD_API_KEY
        self.model = CLOUD_IMAGE_MODEL

    async def generate(self, prompt: str, width: int = 1280, height: int = 720) -> bytes:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "prompt": prompt,
            "size": _supported_size(width, height),
        }
        async with httpx.AsyncClient(timeout=180) as client:
            resp = await client.post(
                f"{self.base_url}/images/generations",
                json=payload,
                headers=headers,
            )
            resp.raise_for_status()
            data = resp.json()

            items = data.get("data") or []
            if not items:
                raise ValueError(f"Unexpected API response format: {list(data.keys())}")

            item = items[0]
            if item.get("b64_json"):
                return base64.b64decode(item["b64_json"])
            if item.get("url"):
                img_resp = await client.get(item["url"])
                img_resp.raise_for_status()
                return img_resp.content
            raise ValueError(f"Unexpected image item keys: {list(item.keys())}")

    async def generate_preview(self, prompt: str, width: int = 640, height: int = 360) -> bytes:
        return await self.generate(prompt, width, height)
