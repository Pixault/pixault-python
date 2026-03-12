"""Fluent builder for Pixault image transformation URLs."""

from __future__ import annotations

from typing import Literal


FitMode = Literal["cover", "contain", "fill", "pad"]
WmPosition = Literal["tl", "tr", "bl", "br", "c", "tile"]
OutputFormat = Literal["jpg", "png", "webp", "avif", "svg"]


class UrlBuilder:
    """
    Fluent builder for Pixault image transformation URLs.

    Example::

        url = pixault.image("tattoo", "img_01JKABC") \\
            .transform("gallery") \\
            .width(800) \\
            .build()
        # => "https://img.pixault.io/tattoo/img_01JKABC/t_gallery,w_800.webp"
    """

    def __init__(self, base_url: str, project: str, image_id: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._project = project
        self._image_id = image_id
        self._params: list[str] = []
        self._format = "webp"
        self._transform_name: str | None = None

    def transform(self, name: str) -> UrlBuilder:
        """Apply a named transform preset."""
        self._transform_name = name
        return self

    def width(self, w: int) -> UrlBuilder:
        """Set the output width in pixels."""
        self._params.append(f"w_{w}")
        return self

    def height(self, h: int) -> UrlBuilder:
        """Set the output height in pixels."""
        self._params.append(f"h_{h}")
        return self

    def fit(self, mode: FitMode) -> UrlBuilder:
        """Set the resize fit mode."""
        self._params.append(f"fit_{mode}")
        return self

    def quality(self, q: int) -> UrlBuilder:
        """Set the output quality (1-100)."""
        self._params.append(f"q_{q}")
        return self

    def blur(self, radius: int) -> UrlBuilder:
        """Apply a Gaussian blur with the given radius."""
        self._params.append(f"blur_{radius}")
        return self

    def watermark(
        self,
        id: str,
        position: WmPosition = "br",
        opacity: int = 30,
    ) -> UrlBuilder:
        """Apply a watermark overlay."""
        self._params.append(f"wm_{id}")
        self._params.append(f"wm_pos_{position}")
        self._params.append(f"wm_opacity_{opacity}")
        return self

    def format(self, fmt: OutputFormat | str) -> UrlBuilder:
        """Set the output format. Default is 'webp'."""
        self._format = fmt.lstrip(".")
        return self

    def build(self) -> str:
        """Build the final CDN URL."""
        all_params: list[str] = []

        if self._transform_name is not None:
            all_params.append(f"t_{self._transform_name}")

        all_params.extend(self._params)

        if not all_params:
            return f"{self._base_url}/{self._project}/{self._image_id}/original.{self._format}"

        joined = ",".join(all_params)
        return f"{self._base_url}/{self._project}/{self._image_id}/{joined}.{self._format}"

    def __str__(self) -> str:
        return self.build()

    def __repr__(self) -> str:
        return f"UrlBuilder({self.build()!r})"
