# Reve 2.1 Edit

> Edit images from text prompts with strong prompt adherence, layout intelligence, and accurate text rendering using Reve 2.1.

## Overview

- **Endpoint**: `https://fal.run/reve/2.1/edit`
- **Model ID**: `reve/2.1/edit`
- **Category**: image-to-image
- **Kind**: inference

## API Information

### Input Schema

- **`prompt`** (`string`, _required_):
  The text description of how to edit the provided image. You can refer to the reference image with `<frame>0</frame>`.

- **`image_url`** (`string`, _required_):
  URL of the reference image to edit. It must be publicly accessible or a base64 data URI. PNG, JPEG, WebP, AVIF, and HEIF are supported.

- **`aspect_ratio`** (`AspectRatioEnum`, _optional_):
  The desired aspect ratio. With `auto`, the model chooses an appropriate ratio. Default: `"auto"`.
  - Options: `"4:1"`, `"3:1"`, `"21:9"`, `"2:1"`, `"17:9"`, `"16:9"`, `"3:2"`, `"4:3"`, `"5:4"`, `"1:1"`, `"4:5"`, `"3:4"`, `"2:3"`, `"9:16"`, `"1:2"`, `"1:3"`, `"1:4"`, `"auto"`

- **`num_images`** (`integer`, _optional_):
  Number of images to generate. Default: `1`.

- **`output_format`** (`OutputFormatEnum`, _optional_):
  Output format. Default: `"png"`.
  - Options: `"png"`, `"jpeg"`, `"webp"`

- **`sync_mode`** (`boolean`, _optional_):
  Return media as a data URI. Default: `false`.

### Required Parameters Example

```json
{
  "prompt": "Give him a friend",
  "image_url": "https://v3b.fal.media/files/b/koala/sZE6zNTKjOKc4kcUdVlu__26bac54c-3e94-43e9-aeff-f2efc2631ef0.webp"
}
```

## Additional Resources

- [Model Playground](https://fal.ai/models/reve/2.1/edit)
- [API Documentation](https://fal.ai/models/reve/2.1/edit/api)
- [LLMs Documentation](https://fal.ai/models/reve/2.1/edit/llms.txt)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=reve/2.1/edit)
