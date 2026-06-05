"""Flipbook — Infinite Visual Browser. FastAPI backend."""

import asyncio
import base64
import io
import json
import logging
from typing import Optional

from PIL import Image

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse, JSONResponse
from pydantic import BaseModel

from . import config
from .models import ImageModel
from .models.mock_model import MockImageModel
from .models.local_model import LocalImageModel
from .models.cloud_model import CloudImageModel
from .understanding import ClickUnderstanding
from .understanding.multimodal import MockClickUnderstanding, LocalClickUnderstanding, CloudClickUnderstanding
from .prompt.builder import build_generation_prompt, build_exploration_prompt
from .prompt.enricher import enrich_prompt, apply_house_style
from .storage.store import store

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("flipbook")

app = FastAPI(title="Flipbook", version="0.1.0")

# CORS — allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Model Initialization ──────────────────────────────────────────────

PROVIDERS = ["mock", "local", "cloud"]


def get_image_model(provider: str) -> ImageModel:
    if provider == "local":
        return LocalImageModel()
    elif provider == "cloud":
        return CloudImageModel()
    else:
        return MockImageModel()


def get_click_understanding(provider: str) -> ClickUnderstanding:
    if provider == "local":
        return LocalClickUnderstanding()
    elif provider == "cloud":
        return CloudClickUnderstanding()
    else:
        return MockClickUnderstanding()


def _make_preview(full_png: bytes, width: int, height: int) -> bytes:
    """Downscale a full image into a small preview (avoids a 2nd generation call)."""
    img = Image.open(io.BytesIO(full_png)).convert("RGB")
    img.thumbnail((width, height))
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


# Server-side DEFAULT provider (used when a request does not specify one).
# The actual provider for each generate/explore call is chosen PER REQUEST so that
# concurrent users do not affect each other.
default_provider = config.MODEL_PROVIDER.lower()
if default_provider not in PROVIDERS:
    default_provider = "mock"


def resolve_provider(requested: Optional[str]) -> str:
    """Pick a valid provider for a request, falling back to the server default."""
    p = (requested or default_provider or "mock").lower()
    return p if p in PROVIDERS else default_provider


def apply_provider(provider: str) -> None:
    """Set the server-side default provider."""
    global default_provider
    default_provider = provider
    logger.info(f"Default provider set to '{provider}'")


logger.info(f"Default provider: {default_provider}")


# ── Request/Response Models ───────────────────────────────────────────

class GenerateRequest(BaseModel):
    query: str
    width: Optional[int] = config.DEFAULT_WIDTH
    height: Optional[int] = config.DEFAULT_HEIGHT
    provider: Optional[str] = None  # per-request provider override


class ExploreRequest(BaseModel):
    page_id: str
    click_x: float  # 0.0 to 1.0 normalized
    click_y: float  # 0.0 to 1.0 normalized
    provider: Optional[str] = None  # per-request provider override


class ProviderRequest(BaseModel):
    provider: str


# ── API Endpoints ─────────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    return {"status": "ok", "model_provider": default_provider}


@app.get("/api/config")
async def get_config():
    """Return the default model provider and the list of available providers.

    The frontend uses `provider` as its initial selection; the actual provider is
    sent per request, so switching never affects other concurrent users.
    """
    return {"provider": default_provider, "providers": PROVIDERS}


@app.post("/api/config")
async def set_config(req: ProviderRequest):
    """Change the server-side DEFAULT provider (optional; per-request still wins)."""
    provider = req.provider.lower()
    if provider not in PROVIDERS:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")
    apply_provider(provider)
    return {"provider": default_provider, "providers": PROVIDERS}


@app.post("/api/generate")
async def generate_page(req: GenerateRequest):
    """Generate a new visual page from a query.

    Returns SSE stream:
    1. First event: page metadata (with preview image as base64)
    2. Second event: full-quality image update
    """
    provider = resolve_provider(req.provider)
    image_model = get_image_model(provider)
    logger.info(f"Generate: query='{req.query}' provider='{provider}'")

    async def event_stream():
        # Rewrite the short query into a rich, structured image prompt (fallback to template)
        content = await enrich_prompt(req.query, provider, mode="generate") \
            or build_generation_prompt(req.query)
        prompt = apply_house_style(content, mode="generate")
        logger.info(f"Generate prompt length={len(prompt)}")

        # Generate the full image once, then derive a small preview from it
        full_data = await image_model.generate(prompt, req.width, req.height)
        preview_data = _make_preview(full_data, config.PREVIEW_WIDTH, config.PREVIEW_HEIGHT)

        page = store.create_page(
            query=req.query,
            prompt=prompt,
            parent_id=None,
            image_data=full_data,
            preview_data=preview_data,
        )

        # Send preview event (page metadata + quick-loading image)
        preview_b64 = base64.b64encode(preview_data).decode()
        preview_event = {
            "type": "preview",
            "page_id": page["id"],
            "query": req.query,
            "image": f"data:image/png;base64,{preview_b64}",
            "breadcrumb": store.get_breadcrumb(page["id"]),
        }
        yield f"data: {json.dumps(preview_event)}\n\n"

        # Send full-quality image event
        full_b64 = base64.b64encode(full_data).decode()
        full_event = {
            "type": "full",
            "page_id": page["id"],
            "image": f"data:image/png;base64,{full_b64}",
        }
        yield f"data: {json.dumps(full_event)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/api/explore")
async def explore_page(req: ExploreRequest):
    """Click on a page to explore deeper — generates a new child page.

    Returns SSE stream (same format as /api/generate).
    """
    parent = store.get_page(req.page_id)
    if not parent:
        raise HTTPException(status_code=404, detail="Page not found")

    # Pass the local image file path so the VL model can read the pixels
    image_url = parent.get("image_path") or parent.get("preview_path") or ""
    parent_query = parent["query"]
    parent_prompt = parent.get("prompt", "")

    provider = resolve_provider(req.provider)
    image_model = get_image_model(provider)
    click_understanding = get_click_understanding(provider)
    logger.info(f"Explore: provider='{provider}'")

    async def event_stream():
        # Step 1: Understand the click and surface the intent to the client immediately
        try:
            click_intent = await click_understanding.understand_click(
                image_url=image_url,
                click_x=req.click_x,
                click_y=req.click_y,
                context=parent_query,
            )
        except Exception as e:
            logger.warning(f"Click understanding failed: {e}")
            click_intent = parent_query
        logger.info(f"Explore: click=({req.click_x:.2f}, {req.click_y:.2f}), intent='{click_intent}'")

        intent_event = {
            "type": "intent",
            "intent": click_intent,
            "parent_id": req.page_id,
        }
        yield f"data: {json.dumps(intent_event)}\n\n"

        # Step 2: Rewrite into a rich deep-dive prompt, then pin the shared house style
        content = await enrich_prompt(
            click_intent,
            provider,
            mode="explore",
            parent_query=parent_query,
            parent_prompt=parent_prompt,
        ) or build_exploration_prompt(click_intent, parent_query)
        prompt = apply_house_style(content, mode="explore")

        # Step 3: Generate the full image once, then derive a small preview from it
        full_data = await image_model.generate(
            prompt, config.DEFAULT_WIDTH, config.DEFAULT_HEIGHT
        )
        preview_data = _make_preview(full_data, config.PREVIEW_WIDTH, config.PREVIEW_HEIGHT)

        page = store.create_page(
            query=click_intent,
            prompt=prompt,
            parent_id=req.page_id,
            image_data=full_data,
            preview_data=preview_data,
        )

        preview_b64 = base64.b64encode(preview_data).decode()
        preview_event = {
            "type": "preview",
            "page_id": page["id"],
            "query": click_intent,
            "image": f"data:image/png;base64,{preview_b64}",
            "breadcrumb": store.get_breadcrumb(page["id"]),
        }
        yield f"data: {json.dumps(preview_event)}\n\n"

        full_b64 = base64.b64encode(full_data).decode()
        full_event = {
            "type": "full",
            "page_id": page["id"],
            "image": f"data:image/png;base64,{full_b64}",
        }
        yield f"data: {json.dumps(full_event)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/api/page/{page_id}")
async def get_page(page_id: str):
    """Get page metadata."""
    page = store.get_page(page_id)
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    return {
        "id": page["id"],
        "query": page["query"],
        "parent_id": page.get("parent_id"),
        "created_at": page["created_at"],
        "has_image": bool(page.get("image_path")),
        "has_preview": bool(page.get("preview_path")),
        "breadcrumb": store.get_breadcrumb(page_id),
    }


@app.get("/api/page/{page_id}/image")
async def get_page_image(page_id: str):
    """Serve the full-quality page image."""
    page = store.get_page(page_id)
    if not page or not page.get("image_path"):
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(page["image_path"], media_type="image/png")


@app.get("/api/page/{page_id}/preview")
async def get_page_preview(page_id: str):
    """Serve the preview page image."""
    page = store.get_page(page_id)
    if not page or not page.get("preview_path"):
        raise HTTPException(status_code=404, detail="Preview not found")
    return FileResponse(page["preview_path"], media_type="image/png")


@app.get("/api/share/{page_id}")
async def share_page(page_id: str):
    """Get a shareable link data for a page."""
    page = store.get_page(page_id)
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    return {
        "page_id": page_id,
        "query": page["query"],
        "share_url": f"/page/{page_id}",
        "breadcrumb": store.get_breadcrumb(page_id),
    }


@app.get("/api/pages")
async def list_pages(limit: int = 50):
    """List all stored pages (for debugging)."""
    pages = []
    import os
    for fname in os.listdir(store.storage_dir):
        if fname.endswith(".json"):
            with open(os.path.join(store.storage_dir, fname)) as f:
                page = json.load(f)
            pages.append({
                "id": page["id"],
                "query": page["query"],
                "created_at": page["created_at"],
            })
    pages.sort(key=lambda p: p["created_at"], reverse=True)
    return {"pages": pages[:limit]}
