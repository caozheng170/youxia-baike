"""Click understanding abstract base class."""

from abc import ABC, abstractmethod


class ClickUnderstanding(ABC):
    """Abstract base class for understanding click intent on images."""

    @abstractmethod
    async def understand_click(
        self,
        image_url: str,
        click_x: float,
        click_y: float,
        context: str,
    ) -> str:
        """Understand what the user wants to explore by clicking on an image.

        Args:
            image_url: URL or local path to the image.
            click_x: X coordinate of click (0.0 to 1.0, normalized).
            click_y: Y coordinate of click (0.0 to 1.0, normalized).
            context: Additional context (e.g., the original query).

        Returns:
            A text description of what the user wants to explore.
        """
        ...
