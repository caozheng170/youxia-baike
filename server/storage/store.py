"""In-memory page storage with file persistence."""

import json
import os
import time
import uuid
from typing import Optional, Dict, Any

from .. import config


class PageStore:
    """Store page data with in-memory cache and optional file persistence."""

    def __init__(self, storage_dir: str = None):
        self.storage_dir = storage_dir or config.STORAGE_DIR
        self._cache: Dict[str, Dict[str, Any]] = {}
        os.makedirs(self.storage_dir, exist_ok=True)

    def create_page(
        self,
        query: str,
        prompt: str,
        parent_id: Optional[str] = None,
        image_data: Optional[bytes] = None,
        preview_data: Optional[bytes] = None,
    ) -> Dict[str, Any]:
        """Create a new page and store it."""
        page_id = str(uuid.uuid4())[:12]
        now = time.time()

        page = {
            "id": page_id,
            "query": query,
            "prompt": prompt,
            "parent_id": parent_id,
            "created_at": now,
            "image_path": None,
            "preview_path": None,
        }

        # Save image files
        if image_data:
            img_dir = os.path.join(self.storage_dir, "images")
            os.makedirs(img_dir, exist_ok=True)
            img_path = os.path.join(img_dir, f"{page_id}.png")
            with open(img_path, "wb") as f:
                f.write(image_data)
            page["image_path"] = img_path

        if preview_data:
            prev_dir = os.path.join(self.storage_dir, "previews")
            os.makedirs(prev_dir, exist_ok=True)
            prev_path = os.path.join(prev_dir, f"{page_id}.png")
            with open(prev_path, "wb") as f:
                f.write(preview_data)
            page["preview_path"] = prev_path

        # Save metadata
        meta_path = os.path.join(self.storage_dir, f"{page_id}.json")
        with open(meta_path, "w") as f:
            json.dump(page, f, indent=2)

        self._cache[page_id] = page
        return page

    def update_image(self, page_id: str, image_data: bytes) -> bool:
        """Update the full-quality image for a page (replacing preview)."""
        page = self.get_page(page_id)
        if not page:
            return False

        img_dir = os.path.join(self.storage_dir, "images")
        os.makedirs(img_dir, exist_ok=True)
        img_path = os.path.join(img_dir, f"{page_id}.png")
        with open(img_path, "wb") as f:
            f.write(image_data)

        page["image_path"] = img_path

        # Persist metadata
        meta_path = os.path.join(self.storage_dir, f"{page_id}.json")
        with open(meta_path, "w") as f:
            json.dump(page, f, indent=2)

        return True

    def get_page(self, page_id: str) -> Optional[Dict[str, Any]]:
        """Get a page by ID."""
        if page_id in self._cache:
            return self._cache[page_id]

        meta_path = os.path.join(self.storage_dir, f"{page_id}.json")
        if os.path.exists(meta_path):
            with open(meta_path, "r") as f:
                page = json.load(f)
            self._cache[page_id] = page
            return page

        return None

    def get_breadcrumb(self, page_id: str) -> list:
        """Get the breadcrumb trail from root to this page."""
        trail = []
        current_id = page_id
        visited = set()

        while current_id and current_id not in visited:
            visited.add(current_id)
            page = self.get_page(current_id)
            if not page:
                break
            trail.append({
                "id": page["id"],
                "query": page["query"],
            })
            current_id = page.get("parent_id")

        trail.reverse()
        return trail


# Global singleton
store = PageStore()
