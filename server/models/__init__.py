"""Image model abstract base class."""

from abc import ABC, abstractmethod
from typing import Optional


class ImageModel(ABC):
    """Abstract base class for image generation models."""

    @abstractmethod
    async def generate(self, prompt: str, width: int = 1280, height: int = 720) -> bytes:
        """Generate a full-quality image from a prompt.

        Args:
            prompt: Text prompt describing the image to generate.
            width: Image width in pixels.
            height: Image height in pixels.

        Returns:
            Image bytes (PNG format).
        """
        ...

    @abstractmethod
    async def generate_preview(self, prompt: str, width: int = 640, height: int = 360) -> bytes:
        """Generate a low-quality preview image from a prompt.

        Args:
            prompt: Text prompt describing the image to generate.
            width: Preview image width in pixels.
            height: Preview image height in pixels.

        Returns:
            Image bytes (PNG format).
        """
        ...
