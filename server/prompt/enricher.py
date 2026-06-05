"""LLM-based prompt enrichment.

Turns a short user topic (e.g. "杭州西湖一日游") into a detailed, structured
image-generation prompt that yields a rich, information-dense infographic:
real content + an appropriate layout archetype + a fitting art style + labels in
the user's language. Falls back gracefully when no text LLM is available.
"""

import logging
import re

import httpx

from .. import config

logger = logging.getLogger("flipbook")


_SYSTEM_BASE = """You are an expert infographic art director and prompt engineer.
Given a TOPIC, write ONE single English image-generation prompt describing the CONTENT and
LAYOUT of a beautiful, information-DENSE infographic. (The painting medium, colors and finish
are fixed separately, so focus on subject, structure and the exact in-image text — do not
spend words on palette or art medium.)

Follow these rules strictly:
1. Pick the BEST layout archetype for the topic:
   - travel / itinerary / a place → a stylized top-down MAP with a numbered route and dashed connecting arrows between illustrated landmarks
   - history / evolution → a horizontal TIMELINE with milestones
   - how-to / process → a step-by-step FLOWCHART with numbered stages and arrows
   - comparison / "vs" → side-by-side COMPARISON panels
   - statistics / data → CHARTS and graphs with labels
   - concept / overview → a central title with a clear HIERARCHY / mind-map of labeled sub-topics
2. Fill it with REAL, SPECIFIC, ACCURATE content about the topic: actual names, places,
   steps, items, numbers and a sensible order. Never leave it vague or generic. Describe the
   small illustrated icons for each element.
3. Always include: a large decorative TITLE at the top, illustrated icons for each element,
   thin leader-line callout annotations with tag-style labels, and a short caption/footer
   banner at the bottom.
4. LANGUAGE OF IN-IMAGE TEXT: ALL text rendered inside the image — the title, every label,
   callout and the footer caption — must be in clear, concise ENGLISH (translate any non-English
   topic into accurate English terms; you may keep a proper noun's romanized name, e.g. "Hu Bi",
   "Anji Bai Cha"). Each label should read as a bold NAME followed by a short descriptive subtitle
   (e.g. "Hu Bi: The Finest Writing Tool").
5. Output ONLY the final image prompt as plain text — no preamble, no markdown, no quotes,
   no explanation. Keep it under 160 words."""

_GENERATE_EXTRA = """
This is an OVERVIEW page. Give a broad, well-organized picture of the whole topic."""

_EXPLORE_EXTRA = """
This is a DEEP-DIVE detail page that zooms into ONE specific aspect. Make it a focused
close-up with detailed leader-line callouts and 1-2 zoomed-in framed detail insets."""


# ── Fixed visual house style (deterministically appended to every prompt) ──────
# Pins every image to the reference aesthetic: refined isometric editorial explainer
# illustration, fine ink line-art with soft watercolour shading, on warm cream
# graph-paper, muted natural palette, leader-line tag labels and English text.
_HOUSE_STYLE = (
    "Art & finish (house style): a refined editorial explainer illustration on a warm cream / "
    "off-white paper background with a faint engineering grid (graph-paper) texture; detailed "
    "hand-drawn fine ink line-art with soft watercolour and colored-pencil shading; isometric / "
    "axonometric 3D vignettes of the objects and scenes where appropriate; a muted, natural, "
    "low-saturation palette of sage and jade greens, warm wood browns, soft greys and beige; a "
    "clear bold title at the top; thin leader lines connecting small rounded tag-style labels "
    "(each a bold name with a short descriptive subtitle) to elements; optional small inset "
    "charts or cutaway diagrams; generous negative space, balanced airy composition, elegant "
    "clean typography, crisp and perfectly legible ENGLISH text; high resolution, intricate detail."
)

_LABEL_ALL_ENGLISH = " Every piece of in-image text (title, labels, callouts, captions) is in clear, concise English."


def apply_house_style(prompt: str, mode: str = "generate") -> str:
    """Append the fixed visual house style so every image matches the reference look."""
    return f"{prompt.strip()}\n\n{_HOUSE_STYLE}{_LABEL_ALL_ENGLISH}"


def _provider_endpoint(provider: str):
    """Return (base_url, api_key, model) for the text LLM of the given provider, or None."""
    if provider == "cloud":
        return config.CLOUD_BASE_URL.rstrip("/"), config.CLOUD_API_KEY, config.CLOUD_TEXT_MODEL
    if provider == "local":
        return config.LOCAL_XINFERENCE_URL.rstrip("/") + "/v1", config.LOCAL_API_KEY, config.LOCAL_LLM_MODEL
    return None  # mock has no text LLM


def _clean(text: str) -> str:
    text = text.strip()
    # Strip markdown code fences if the model wrapped the output
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text).strip()
    # Strip a single pair of surrounding quotes
    if len(text) >= 2 and text[0] in "\"'“" and text[-1] in "\"'”":
        text = text[1:-1].strip()
    return text


async def enrich_prompt(
    topic: str,
    provider: str,
    mode: str = "generate",
    parent_query: str = "",
    parent_prompt: str = "",
) -> str | None:
    """Use the active provider's text LLM to expand `topic` into a rich image prompt.

    Returns the enriched prompt, or None if enrichment is unavailable/failed
    (caller should fall back to the template builder).
    """
    endpoint = _provider_endpoint(provider)
    if not endpoint:
        return None
    base_url, api_key, model = endpoint

    system = _SYSTEM_BASE + (_EXPLORE_EXTRA if mode == "explore" else _GENERATE_EXTRA)

    user_parts = [f"TOPIC: {topic}"]
    if mode == "explore" and parent_query:
        user_parts.append(f"This is a deeper exploration of the parent topic: {parent_query}")
    if mode == "explore" and parent_prompt:
        user_parts.append(f"PARENT infographic prompt (match its style):\n{parent_prompt}")
    user = "\n\n".join(user_parts)

    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{base_url}/chat/completions",
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "temperature": 0.7,
                    "max_tokens": 600,
                },
                headers=headers,
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        logger.warning(f"Prompt enrichment failed ({provider}/{model}): {e}")
        return None

    enriched = _clean(content or "")
    if len(enriched) < 20:
        logger.warning("Prompt enrichment returned too little text; using fallback.")
        return None

    logger.info(f"Enriched prompt ({mode}) len={len(enriched)}")
    return enriched
