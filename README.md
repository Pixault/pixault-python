# pixault

Python SDK for the [Pixault](https://pixault.io) image processing CDN and API.

## Requirements

- Python 3.10+

## Installation

```bash
pip install pixault
```

## Quick Start

```python
from pixault import Pixault

px = Pixault(
    base_url="https://img.pixault.io",
    default_project="my-project",
    client_id="px_cl_a1b2c3d4",
    client_secret="pk_...",
)

# Generate an optimized image URL
url = px.image("img_01JKABC") \
    .width(800) \
    .height(600) \
    .fit("cover") \
    .quality(85) \
    .format("webp") \
    .build()
# => "https://img.pixault.io/my-project/img_01JKABC/w_800,h_600,fit_cover,q_85.webp"

# Upload an image
result = px.upload("my-project", "photo.jpg")
print(result["imageId"])

# List images
images = px.list_images("my-project", category="hero")

# Get metadata
meta = px.get_metadata("my-project", "img_01JKABC")
```

## URL Builder

```python
# Named transform with overrides
url = px.image("my-project", "img_01JKABC") \
    .transform("gallery") \
    .width(400) \
    .build()

# Watermark
url = px.image("img_01JKABC") \
    .width(1200) \
    .watermark("logo", "br", 30) \
    .build()
```

## Context Manager

```python
with Pixault(base_url="https://img.pixault.io") as px:
    result = px.upload("my-project", "photo.jpg")
```

## Configuration

| Parameter | Description | Required |
|-----------|-------------|----------|
| `base_url` | Pixault CDN base URL | Yes |
| `default_project` | Default project ID | No |
| `client_id` | API key client ID (`px_cl_...`) | No |
| `client_secret` | API key secret (`pk_...`) | No |

## Documentation

Full documentation at [pixault.dev](https://pixault.dev).

## License

[MIT](LICENSE)
