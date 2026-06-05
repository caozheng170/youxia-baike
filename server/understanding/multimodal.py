"""Mock click understanding — uses prompt heuristics."""

import random
import hashlib

from . import ClickUnderstanding


# Topic expansion templates for mock understanding
EXPANSION_TEMPLATES = [
    "Explore the details of {topic} — show visual breakdown of key concepts",
    "Deep dive into {topic} — information architecture and connections",
    "Inside {topic} — visual map of components and relationships",
    "Zooming into {topic} — detailed infographic with sub-elements",
    "{topic} — expanded view with annotations and data points",
]

# Region-based hints (quadrants of the image)
REGION_HINTS = {
    (0, 0): "top-left section, likely an overview or title area",
    (1, 0): "top-right section, likely a key detail or highlight",
    (0, 1): "bottom-left section, likely supporting information",
    (1, 1): "bottom-right section, likely conclusions or next steps",
}


class MockClickUnderstanding(ClickUnderstanding):
    """Mock understanding that uses heuristic rules."""

    async def understand_click(
        self,
        image_url: str,
        click_x: float,
        click_y: float,
        context: str,
    ) -> str:
        # Determine which quadrant was clicked
        qx = 1 if click_x > 0.5 else 0
        qy = 1 if click_y > 0.5 else 0
        region_hint = REGION_HINTS.get((qx, qy), "central area")

        # Extract topic from context (use the query if available)
        topic = context if context else "this topic"

        # Pick a template deterministically based on click position
        rng = random.Random(hash(f"{click_x:.3f}:{click_y:.3f}:{context}"))
        template = rng.choice(EXPANSION_TEMPLATES)

        expansion = template.format(topic=topic)
        return f"{expansion} (clicked {region_hint})"


def _build_click_prompt(click_x: float, click_y: float, context: str) -> str:
    return (
        f"The user clicked at position ({click_x:.2f}, {click_y:.2f}) on this image "
        f"(coordinates are normalized 0-1, origin at top-left). "
        f"The original query was: '{context}'. "
        f"What topic or element at that position would the user want to explore further? "
        f"Reply with a single concise topic phrase IN ENGLISH (no explanation, no quotes) "
        f"for generating a new infographic."
    )


async def _load_image_b64(image_url: str) -> str:
    """Load an image (file path or http url) and return base64 string, or '' if unavailable."""
    import os
    import httpx
    import base64

    if not image_url:
        return ""
    try:
        if image_url.startswith(("http://", "https://")):
            async with httpx.AsyncClient(timeout=30) as client:
                img_resp = await client.get(image_url)
                img_resp.raise_for_status()
                return base64.b64encode(img_resp.content).decode()
        if os.path.exists(image_url):
            with open(image_url, "rb") as f:
                return base64.b64encode(f.read()).decode()
    except Exception:
        return ""
    return ""


async def _chat_understand(
    base_url: str,
    api_key: str,
    model: str,
    image_url: str,
    click_x: float,
    click_y: float,
    context: str,
) -> str:
    """Shared OpenAI-compatible vision chat-completion call for click understanding."""
    import httpx

    prompt = _build_click_prompt(click_x, click_y, context)
    img_b64 = await _load_image_b64(image_url)

    content = [{"type": "text", "text": prompt}]
    if img_b64:
        content.insert(
            0,
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}},
        )

    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            f"{base_url}/chat/completions",
            json={
                "model": model,
                "messages": [{"role": "user", "content": content}],
                "max_tokens": 200,
                "temperature": 0.3,
            },
            headers=headers,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()


class LocalClickUnderstanding(ClickUnderstanding):
    """Use a local multimodal model (Qwen via Xinference) for click understanding."""

    def __init__(self):
        from ..config import LOCAL_XINFERENCE_URL, LOCAL_VL_MODEL, LOCAL_API_KEY
        self.base_url = LOCAL_XINFERENCE_URL.rstrip("/") + "/v1"
        self.model = LOCAL_VL_MODEL
        self.api_key = LOCAL_API_KEY

    async def understand_click(
        self,
        image_url: str,
        click_x: float,
        click_y: float,
        context: str,
    ) -> str:
        return await _chat_understand(
            self.base_url, self.api_key, self.model, image_url, click_x, click_y, context
        )


class CloudClickUnderstanding(ClickUnderstanding):
    """Use a cloud multimodal model (OpenAI-compatible API) for click understanding."""

    def __init__(self):
        from ..config import CLOUD_BASE_URL, CLOUD_API_KEY, CLOUD_VL_MODEL
        self.base_url = CLOUD_BASE_URL.rstrip("/")
        self.api_key = CLOUD_API_KEY
        self.model = CLOUD_VL_MODEL

    async def understand_click(
        self,
        image_url: str,
        click_x: float,
        click_y: float,
        context: str,
    ) -> str:
        return await _chat_understand(
            self.base_url, self.api_key, self.model, image_url, click_x, click_y, context
        )
