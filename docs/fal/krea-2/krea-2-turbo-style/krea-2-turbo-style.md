# Krea 2 Text to Image Turbo Style

> Generate high-fidelity images from text with Krea 2 using a style reference image. Apply a reference image to guide the visual style into new generations, with aspect ratio, creativity, and seed controls.


## Overview

- **Endpoint**: `https://fal.run/fal-ai/krea-2/turbo/style`
- **Model ID**: `fal-ai/krea-2/turbo/style`
- **Category**: text-to-image
- **Kind**: inference
**Description**: Krea 2 Turbo Style generates high-fidelity images from text while using a reference image to guide the visual style. Provide a clear prompt and a style reference to carry its color palette, lighting, texture, composition, and overall art direction into new images.

Use it for consistent brand visuals, editorial illustration, product concepts, and stylized creative exploration. Control aspect ratio, creativity, and seed to tailor output composition and reproducibility.

**Tags**: stylized, style transfer, reference image, realism



## Pricing

- **Price**: $0.01 per megapixels

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _required_):
  Base text description of the image to generate.
  - Examples: "a vintage travel poster for Mars"

- **`seed`** (`integer`, _optional_):
  Random seed for reproducible generation. Image *i* uses `seed + i`.

- **`image_size`** (`ImageSize | Enum`, _optional_):
  The size of the generated image. Default value: `square_hd`
  - Default: `"square_hd"`
  - One of: ImageSize | Enum

- **`num_images`** (`integer`, _optional_):
  The number of images to generate. Default value: `1`
  - Default: `1`
  - Range: `1` to `4`

- **`acceleration`** (`AccelerationEnum`, _optional_):
  The acceleration level to use for the image generation. Default value: `"none"`
  - Default: `"none"`
  - Options: `"none"`, `"regular"`

- **`enable_prompt_expansion`** (`boolean`, _optional_):
  If true, the prompt is expanded with an LLM into a more detailed image-generation prompt for higher quality results. On failure, the original prompt is used unchanged.
  - Default: `false`

- **`sync_mode`** (`boolean`, _optional_):
  If `True`, the media will be returned as a data URI and the output data won't be available in the request history.
  - Default: `false`

- **`enable_safety_checker`** (`boolean`, _optional_):
  If true, the output safety checker is enabled. Default value: `true`
  - Default: `true`

- **`output_format`** (`OutputFormatEnum`, _optional_):
  The format of the generated image. Default value: "png". Default value: `"png"`
  - Default: `"png"`
  - Options: `"jpeg"`, `"png"`

- **`reference_image_urls`** (`list<string>`, _required_):
  One to three image URLs used as style references.
  - Array of string

- **`style_scale`** (`float`, _optional_):
  Scale for the style adapter residual. Default value: `1`
  - Default: `1`
  - Range: `0` to `4`



**Required Parameters Example**:

```json
{
  "prompt": "a vintage travel poster for Mars"
}
```

**Full Example**:

```json
{
  "prompt": "a vintage travel poster for Mars",
  "image_size": "square_hd",
  "num_images": 1,
  "acceleration": "none",
  "enable_safety_checker": true,
  "output_format": "png",
  "style_scale": 1
}
```


### Output Schema

The API returns the following output format:

- **`images`** (`list<ImageFile>`, _required_):
  The generated images.
  - Array of ImageFile

- **`timings`** (`Timings`, _required_):
  Timing information for the request, in seconds.

- **`seed`** (`integer`, _required_):
  The seed used to generate the image(s).
  - Examples: 12345

- **`has_nsfw_concepts`** (`list<boolean>`, _required_):
  Whether each generated image contains NSFW concepts.
  - Array of boolean

- **`prompt`** (`string`, _required_):
  The prompt used for generation.

- **`actual_prompt`** (`string`, _optional_):
  The final prompt after expansion, if prompt expansion was enabled.



**Example Response**:

```json
{
  "images": [
    {
      "url": "",
      "content_type": "image/png",
      "file_name": "z9RV14K95DvU.png",
      "file_size": 4404019
    }
  ],
  "seed": 12345,
  "prompt": ""
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/krea-2/turbo/style \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "a vintage travel poster for Mars"
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
    "fal-ai/krea-2/turbo/style",
    arguments={
        "prompt": "a vintage travel poster for Mars"
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

const result = await fal.subscribe("fal-ai/krea-2/turbo/style", {
  input: {
    prompt: "a vintage travel poster for Mars"
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

- [Model Playground](https://fal.ai/models/fal-ai/krea-2/turbo/style)
- [API Documentation](https://fal.ai/models/fal-ai/krea-2/turbo/style/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/krea-2/turbo/style)

### fal.ai Platform

- [Platform Documentation](https://docs.fal.ai)
- [Python Client](https://docs.fal.ai/clients/python)
- [JavaScript Client](https://docs.fal.ai/clients/javascript)
