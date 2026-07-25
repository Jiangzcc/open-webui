# Recraft V3

> Recraft V3 is a text-to-image model with the ability to generate long texts, vector art, images in brand style, and much more. As of today, it is SOTA in image generation, proven by Hugging Face's industry-leading Text-to-Image Benchmark by Artificial Analysis.


## Overview

- **Endpoint**: `https://fal.run/fal-ai/recraft/v3/image-to-image`
- **Model ID**: `fal-ai/recraft/v3/image-to-image`
- **Category**: image-to-image
- **Kind**: inference
**Tags**: vector, typography, style



## Pricing

Your request will cost **$0.04** per image (or **$0.08** if you are using a vector style). For $1 you can run this model approximately **25** times.

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _required_):
  A text description of areas to change.
  - Examples: "winter", "cyberpunk city", "watercolor painting style"

- **`image_url`** (`string`, _required_):
  The URL of the image to modify. Must be less than 5 MB in size, have resolution less than 16 MP and max dimension less than 4096 pixels.
  - Examples: "https://storage.googleapis.com/falserverless/model_tests/recraft/recraft-upscaler-1.jpeg"

- **`strength`** (`float`, _optional_):
  Defines the difference with the original image, should lie in [0, 1], where 0 means almost identical, and 1 means miserable similarity Default value: `0.5`
  - Default: `0.5`
  - Range: `0` to `1`
  - Examples: 0.2, 0.5, 0.8

- **`style`** (`StyleEnum`, _optional_):
  The style of the generated images. Vector images cost 2X as much. Default value: `"realistic_image"`
  - Default: `"realistic_image"`
  - Options: `"any"`, `"realistic_image"`, `"digital_illustration"`, `"vector_illustration"`, `"realistic_image/b_and_w"`, `"realistic_image/hard_flash"`, `"realistic_image/hdr"`, `"realistic_image/natural_light"`, `"realistic_image/studio_portrait"`, `"realistic_image/enterprise"`, `"realistic_image/motion_blur"`, `"realistic_image/evening_light"`, `"realistic_image/faded_nostalgia"`, `"realistic_image/forest_life"`, `"realistic_image/mystic_naturalism"`, `"realistic_image/natural_tones"`, `"realistic_image/organic_calm"`, `"realistic_image/real_life_glow"`, `"realistic_image/retro_realism"`, `"realistic_image/retro_snapshot"`, `"realistic_image/urban_drama"`, `"realistic_image/village_realism"`, `"realistic_image/warm_folk"`, `"digital_illustration/pixel_art"`, `"digital_illustration/hand_drawn"`, `"digital_illustration/grain"`, `"digital_illustration/infantile_sketch"`, `"digital_illustration/2d_art_poster"`, `"digital_illustration/handmade_3d"`, `"digital_illustration/hand_drawn_outline"`, `"digital_illustration/engraving_color"`, `"digital_illustration/2d_art_poster_2"`, `"digital_illustration/antiquarian"`, `"digital_illustration/bold_fantasy"`, `"digital_illustration/child_book"`, `"digital_illustration/child_books"`, `"digital_illustration/cover"`, `"digital_illustration/crosshatch"`, `"digital_illustration/digital_engraving"`, `"digital_illustration/expressionism"`, `"digital_illustration/freehand_details"`, `"digital_illustration/grain_20"`, `"digital_illustration/graphic_intensity"`, `"digital_illustration/hard_comics"`, `"digital_illustration/long_shadow"`, `"digital_illustration/modern_folk"`, `"digital_illustration/multicolor"`, `"digital_illustration/neon_calm"`, `"digital_illustration/noir"`, `"digital_illustration/nostalgic_pastel"`, `"digital_illustration/outline_details"`, `"digital_illustration/pastel_gradient"`, `"digital_illustration/pastel_sketch"`, `"digital_illustration/pop_art"`, `"digital_illustration/pop_renaissance"`, `"digital_illustration/street_art"`, `"digital_illustration/tablet_sketch"`, `"digital_illustration/urban_glow"`, `"digital_illustration/urban_sketching"`, `"digital_illustration/vanilla_dreams"`, `"digital_illustration/young_adult_book"`, `"digital_illustration/young_adult_book_2"`, `"vector_illustration/bold_stroke"`, `"vector_illustration/chemistry"`, `"vector_illustration/colored_stencil"`, `"vector_illustration/contour_pop_art"`, `"vector_illustration/cosmics"`, `"vector_illustration/cutout"`, `"vector_illustration/depressive"`, `"vector_illustration/editorial"`, `"vector_illustration/emotional_flat"`, `"vector_illustration/infographical"`, `"vector_illustration/marker_outline"`, `"vector_illustration/mosaic"`, `"vector_illustration/naivector"`, `"vector_illustration/roundish_flat"`, `"vector_illustration/segmented_colors"`, `"vector_illustration/sharp_contrast"`, `"vector_illustration/thin"`, `"vector_illustration/vector_photo"`, `"vector_illustration/vivid_shapes"`, `"vector_illustration/engraving"`, `"vector_illustration/line_art"`, `"vector_illustration/line_circuit"`, `"vector_illustration/linocut"`

- **`colors`** (`list<RGBColor>`, _optional_):
  An array of preferable colors
  - Default: `[]`
  - Array of RGBColor

- **`style_id`** (`string`, _optional_):
  The ID of the custom style reference (optional)
  - Examples: null

- **`negative_prompt`** (`string`, _optional_):
  A text description of undesired elements on an image

- **`sync_mode`** (`boolean`, _optional_):
  If `True`, the media will be returned as a data URI and the output data won't be available in the request history.
  - Default: `false`



**Required Parameters Example**:

```json
{
  "prompt": "winter",
  "image_url": "https://storage.googleapis.com/falserverless/model_tests/recraft/recraft-upscaler-1.jpeg"
}
```

**Full Example**:

```json
{
  "prompt": "winter",
  "image_url": "https://storage.googleapis.com/falserverless/model_tests/recraft/recraft-upscaler-1.jpeg",
  "strength": 0.2,
  "style": "realistic_image",
  "colors": [],
  "style_id": null
}
```


### Output Schema

The API returns the following output format:

- **`images`** (`list<File>`, _required_):
  The generated images
  - Array of File
  - Examples: [{"url":"https://v3.fal.media/files/koala/Xoz8tel7YoTbh6Fiepmq3_image.webp"}]



**Example Response**:

```json
{
  "images": [
    {
      "url": "https://v3.fal.media/files/koala/Xoz8tel7YoTbh6Fiepmq3_image.webp"
    }
  ]
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/recraft/v3/image-to-image \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "winter",
     "image_url": "https://storage.googleapis.com/falserverless/model_tests/recraft/recraft-upscaler-1.jpeg"
   }'
```

### Python

Ensure you have the Python client installed:

```bash
pip install fal-client
```

Then use the API client to make requests:

```python
import fal_client

def on_queue_update(update):
    if isinstance(update, fal_client.InProgress):
        for log in update.logs:
           print(log["message"])

result = fal_client.subscribe(
    "fal-ai/recraft/v3/image-to-image",
    arguments={
        "prompt": "winter",
        "image_url": "https://storage.googleapis.com/falserverless/model_tests/recraft/recraft-upscaler-1.jpeg"
    },
    with_logs=True,
    on_queue_update=on_queue_update,
)
print(result)
```

### JavaScript

Ensure you have the JavaScript client installed:

```bash
npm install --save @fal-ai/client
```

Then use the API client to make requests:

```javascript
import { fal } from "@fal-ai/client";

const result = await fal.subscribe("fal-ai/recraft/v3/image-to-image", {
  input: {
    prompt: "winter",
    image_url: "https://storage.googleapis.com/falserverless/model_tests/recraft/recraft-upscaler-1.jpeg"
  },
  logs: true,
  onQueueUpdate: (update) => {
    if (update.status === "IN_PROGRESS") {
      update.logs.map((log) => log.message).forEach(console.log);
    }
  },
});
console.log(result.data);
console.log(result.requestId);
```


## Additional Resources

### Documentation

- [Model Playground](https://fal.ai/models/fal-ai/recraft/v3/image-to-image)
- [API Documentation](https://fal.ai/models/fal-ai/recraft/v3/image-to-image/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/recraft/v3/image-to-image)

### fal.ai Platform

- [Platform Documentation](https://docs.fal.ai)
- [Python Client](https://docs.fal.ai/clients/python)
- [JavaScript Client](https://docs.fal.ai/clients/javascript)
