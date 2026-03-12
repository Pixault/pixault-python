"""Pixault SDK client — URL generation, upload, and image management."""

from __future__ import annotations

from pathlib import Path
from typing import Any, BinaryIO

import httpx

from pixault.url_builder import UrlBuilder


class PixaultError(Exception):
    """Error raised by the Pixault API."""

    def __init__(self, message: str, status_code: int = 0) -> None:
        super().__init__(message)
        self.status_code = status_code


class Pixault:
    """
    Pixault SDK client — URL generation, upload, and image management.

    Example::

        from pixault import Pixault

        px = Pixault(
            base_url="https://img.pixault.io",
            default_project="barber",
            client_id="px_cl_a1b2c3d4",
            client_secret="pk_...",
        )

        # Generate URLs
        url = px.image("img_01JKABC").width(800).build()

        # Upload
        result = px.upload("barber", "photo.jpg")

        # Metadata
        meta = px.get_metadata("barber", "img_01JKABC")
    """

    def __init__(
        self,
        base_url: str,
        default_project: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
        api_key: str | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._default_project = default_project
        self._client_id = client_id
        self._client_secret = client_secret
        self._api_key = api_key  # Legacy fallback
        self._client = httpx.Client(
            base_url=self._base_url,
            headers=self._build_headers(),
            timeout=60.0,
        )

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._client.close()

    def __enter__(self) -> Pixault:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    # ── URL builder ──

    def image(self, project_or_id: str, image_id: str | None = None) -> UrlBuilder:
        """
        Create a URL builder.

        Call as ``image(project, image_id)`` or ``image(image_id)`` with a default project.
        """
        if image_id is not None:
            return UrlBuilder(self._base_url, project_or_id, image_id)

        if self._default_project is None:
            raise ValueError(
                "default_project must be set when calling image() without a project."
            )
        return UrlBuilder(self._base_url, self._default_project, project_or_id)

    # ── Upload ──

    def upload(
        self,
        project: str,
        file: str | Path | BinaryIO,
        *,
        file_name: str | None = None,
        name: str | None = None,
        description: str | None = None,
        caption: str | None = None,
        category: str | None = None,
        keywords: str | None = None,
        author: str | None = None,
    ) -> dict[str, Any]:
        """
        Upload an image file.

        ``file`` can be a file path (str/Path) or a file-like object.

        Returns a dict with ``imageId``, ``url``, ``width``, ``height``, ``size``.
        """
        if isinstance(file, (str, Path)):
            path = Path(file)
            resolved_name = file_name or path.name
            fp: BinaryIO = open(path, "rb")  # noqa: SIM115
            should_close = True
        else:
            resolved_name = file_name or getattr(file, "name", "upload")
            fp = file
            should_close = False

        try:
            files = {"file": (resolved_name, fp)}

            data: dict[str, str] = {}
            for key, value in [
                ("name", name),
                ("description", description),
                ("caption", caption),
                ("category", category),
                ("keywords", keywords),
                ("author", author),
            ]:
                if value is not None:
                    data[key] = value

            response = self._client.post(
                f"/api/{project}/upload",
                files=files,
                data=data if data else None,
            )
            self._check_response(response)
            return response.json()
        finally:
            if should_close:
                fp.close()

    # ── List / Search ──

    def list_images(
        self,
        project: str,
        *,
        search: str | None = None,
        category: str | None = None,
        keyword: str | None = None,
        author: str | None = None,
        is_video: bool | None = None,
        limit: int = 50,
        cursor: str | None = None,
    ) -> dict[str, Any]:
        """
        List images with optional filtering.

        Example::

            result = px.list_images("barber")
            tattoos = px.list_images("barber", category="tattoo-flash")
            page2 = px.list_images("barber", cursor=result["nextCursor"])

        Returns a dict with ``images``, ``nextCursor``, ``totalCount``.
        """
        params: dict[str, str] = {"limit": str(limit)}
        if cursor:
            params["cursor"] = cursor
        if search:
            params["search"] = search
        if category:
            params["category"] = category
        if keyword:
            params["keyword"] = keyword
        if author:
            params["author"] = author
        if is_video is not None:
            params["isVideo"] = str(is_video).lower()

        response = self._client.get(f"/api/{project}/images", params=params)
        self._check_response(response)
        return response.json()

    # ── Delete ──

    def delete(self, project: str, image_id: str) -> None:
        """Delete an image and all its cached variants."""
        response = self._client.delete(f"/api/{project}/{image_id}")
        self._check_response(response)

    # ── Metadata ──

    def get_metadata(self, project: str, image_id: str) -> dict[str, Any] | None:
        """Get metadata for an image. Returns None if not found."""
        response = self._client.get(f"/api/{project}/{image_id}/metadata")
        if response.status_code == 404:
            return None
        self._check_response(response)
        return response.json()

    def update_metadata(
        self, project: str, image_id: str, **updates: Any
    ) -> dict[str, Any]:
        """
        Update metadata fields. Only provided keyword arguments are overwritten.

        Example::

            px.update_metadata("barber", "img_01JKABC",
                name="Hero shot", caption="Alt text for SEO")
        """
        response = self._client.patch(
            f"/api/{project}/{image_id}/metadata",
            json=updates,
        )
        self._check_response(response)
        return response.json()

    def get_jsonld(self, project: str, image_id: str) -> dict[str, Any] | None:
        """Get Schema.org JSON-LD for an image."""
        response = self._client.get(f"/api/{project}/{image_id}/metadata/jsonld")
        if response.status_code == 404:
            return None
        self._check_response(response)
        return response.json()

    # ── EPS Operations ──

    def list_derived(self, project: str, image_id: str) -> list[dict[str, Any]]:
        """List derived assets (rasterized PNGs, SVGs, splits) for an EPS parent."""
        response = self._client.get(f"/api/{project}/{image_id}/derived")
        self._check_response(response)
        return response.json()

    def get_processing_status(self, project: str, image_id: str) -> dict[str, Any] | None:
        """Get the processing status for an EPS file. Returns None if no job found."""
        response = self._client.get(f"/api/{project}/{image_id}/processing-status")
        if response.status_code == 404:
            return None
        self._check_response(response)
        return response.json()

    def split_designs(self, project: str, image_id: str) -> None:
        """Trigger auto-split to extract individual designs from an EPS file."""
        response = self._client.post(f"/api/{project}/{image_id}/split")
        self._check_response(response)

    def extract_svg(self, project: str, image_id: str) -> None:
        """Trigger vector SVG extraction from an EPS file."""
        response = self._client.post(f"/api/{project}/{image_id}/extract-svg")
        self._check_response(response)

    # ── Internal ──

    def _build_headers(self) -> dict[str, str]:
        headers: dict[str, str] = {}
        if self._client_id:
            headers["X-Client-Id"] = self._client_id
        if self._client_secret:
            headers["X-Client-Secret"] = self._client_secret
        elif self._api_key:
            # Legacy fallback
            headers["X-Api-Key"] = self._api_key
        return headers

    @staticmethod
    def _check_response(response: httpx.Response) -> None:
        if response.status_code >= 400:
            message = f"Pixault API error: {response.status_code}"
            try:
                body = response.json()
                if "error" in body:
                    message = body["error"]
            except Exception:
                pass
            raise PixaultError(message, response.status_code)
