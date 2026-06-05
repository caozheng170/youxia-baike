"""Local image model using Xinference (OpenAI-compatible)."""

import base64
import httpx
from . import ImageModel
from ..config import LOCAL_XINFERENCE_URL, LOCAL_IMAGE_MODEL, LOCAL_API_KEY


class LocalImageModel(ImageModel):
    """Generate images via a local Xinference server."""

    def __init__(self):
        self.base_url = LOCAL_XINFERENCE_URL.rstrip("/")
        self.model = LOCAL_IMAGE_MODEL
        self.api_key = LOCAL_API_KEY

    async def generate(self, prompt: str, width: int = 1280, height: int = 720) -> bytes:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        async with httpx.AsyncClient(timeout=180) as client:
            resp = await client.post(
                f"{self.base_url}/v1/images/generations",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "n": 1,
                    "size": f"{width}x{height}",
                    "response_format": "b64_json",
                },
                headers=headers,
            )
            resp.raise_for_status()
            item = resp.json()["data"][0]
            if item.get("b64_json"):
                return base64.b64decode(item["b64_json"])
            if item.get("url"):
                img_resp = await client.get(item["url"])
                img_resp.raise_for_status()
                return img_resp.content
            raise ValueError(f"Unexpected image response keys: {list(item.keys())}")

    async def generate_preview(self, prompt: str, width: int = 640, height: int = 360) -> bytes:
        # Preview uses smaller size for speed
        return await self.generate(prompt, width, height)
