"""Mock image model for development — generates placeholder images."""

import io
import math
import random
import hashlib
from PIL import Image, ImageDraw, ImageFont

from . import ImageModel


# Warm, earthy color palette matching flipbook aesthetic
PALETTE = [
    (235, 225, 209),  # #ebe1d1 - warm parchment
    (200, 180, 150),  # warm tan
    (170, 140, 100),  # wood brown
    (120, 90, 60),    # dark wood
    (80, 60, 40),     # deep brown
    (210, 160, 100),  # honey
    (180, 120, 80),   # amber
    (150, 100, 70),   # chestnut
]


def _hash_color(text: str) -> tuple:
    """Derive a deterministic color from text."""
    h = hashlib.md5(text.encode()).hexdigest()
    r = int(h[0:2], 16) % 80 + 140
    g = int(h[2:4], 16) % 80 + 100
    b = int(h[4:6], 16) % 60 + 60
    return (r, g, b)


def _generate_placeholder(prompt: str, width: int, height: int, quality: str = "full") -> bytes:
    """Generate a visually interesting placeholder image.

    Args:
        prompt: The generation prompt (used to derive colors and layout).
        width: Image width.
        height: Image height.
        quality: "preview" for fast/simple, "full" for detailed.
    """
    img = Image.new("RGB", (width, height), (235, 225, 209))
    draw = ImageDraw.Draw(img)

    # Background gradient
    base_color = _hash_color(prompt)
    for y in range(height):
        factor = y / height
        r = int(235 + (base_color[0] - 235) * factor * 0.6)
        g = int(225 + (base_color[1] - 225) * factor * 0.6)
        b = int(209 + (base_color[2] - 209) * factor * 0.6)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # Decorative geometric shapes (seeded by prompt)
    rng = random.Random(hashlib.md5(prompt.encode()).hexdigest())
    n_shapes = 12 if quality == "full" else 6

    for _ in range(n_shapes):
        shape_type = rng.choice(["circle", "rect", "line"])
        x = rng.randint(0, width)
        y = rng.randint(0, height)
        size = rng.randint(20, min(width, height) // 4)
        alpha_color = tuple(rng.randint(60, 180) for _ in range(3))

        if shape_type == "circle":
            draw.ellipse([x - size, y - size, x + size, y + size], outline=alpha_color, width=2)
        elif shape_type == "rect":
            draw.rectangle([x, y, x + size, y + size * 2 // 3], outline=alpha_color, width=2)
        else:
            x2 = x + rng.randint(-width // 3, width // 3)
            y2 = y + rng.randint(-height // 3, height // 3)
            draw.line([(x, y), (x2, y2)], fill=alpha_color, width=2)

    # Title text
    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", min(width, height) // 12)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", min(width, height) // 24)
    except (OSError, IOError):
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # Draw the query as title
    title = prompt[:60] + ("..." if len(prompt) > 60 else "")
    # Get text bounding box
    bbox = draw.textbbox((0, 0), title, font=font_large)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    tx = (width - tw) // 2
    ty = height // 3 - th // 2

    # Text shadow
    draw.text((tx + 2, ty + 2), title, fill=(60, 40, 20), font=font_large)
    draw.text((tx, ty), title, fill=(80, 60, 40), font=font_large)

    # Subtitle
    subtitle = "🔍 Click anywhere to explore deeper" if quality == "full" else "Generating..."
    bbox2 = draw.textbbox((0, 0), subtitle, font=font_small)
    tw2 = bbox2[2] - bbox2[0]
    draw.text(((width - tw2) // 2, ty + th + 20), subtitle, fill=(120, 100, 80), font=font_small)

    # Decorative corner marks
    corner_size = 30
    corner_color = (170, 140, 100)
    # Top-left
    draw.line([(20, 20), (20 + corner_size, 20)], fill=corner_color, width=3)
    draw.line([(20, 20), (20, 20 + corner_size)], fill=corner_color, width=3)
    # Top-right
    draw.line([(width - 20, 20), (width - 20 - corner_size, 20)], fill=corner_color, width=3)
    draw.line([(width - 20, 20), (width - 20, 20 + corner_size)], fill=corner_color, width=3)
    # Bottom-left
    draw.line([(20, height - 20), (20 + corner_size, height - 20)], fill=corner_color, width=3)
    draw.line([(20, height - 20), (20, height - 20 - corner_size)], fill=corner_color, width=3)
    # Bottom-right
    draw.line([(width - 20, height - 20), (width - 20 - corner_size, height - 20)], fill=corner_color, width=3)
    draw.line([(width - 20, height - 20), (width - 20, height - 20 - corner_size)], fill=corner_color, width=3)

    # Mock badge
    if quality == "preview":
        badge_text = "PREVIEW"
        badge_bbox = draw.textbbox((0, 0), badge_text, font=font_small)
        bw = badge_bbox[2] - badge_bbox[0] + 16
        bh = badge_bbox[3] - badge_bbox[1] + 8
        draw.rectangle([width - bw - 10, 10, width - 10, 10 + bh], fill=(200, 160, 100))
        draw.text((width - bw - 2, 14), badge_text, fill=(255, 255, 255), font=font_small)

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


class MockImageModel(ImageModel):
    """Generates placeholder images for development."""

    async def generate(self, prompt: str, width: int = 1280, height: int = 720) -> bytes:
        return _generate_placeholder(prompt, width, height, quality="full")

    async def generate_preview(self, prompt: str, width: int = 640, height: int = 360) -> bytes:
        return _generate_placeholder(prompt, width, height, quality="preview")
