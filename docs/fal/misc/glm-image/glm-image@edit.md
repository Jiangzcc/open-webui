# Glm Image

> Create high-quality images with accurate text rendering and rich knowledge details—supports editing, style transfer, and maintaining consistent characters across multiple images.


## Overview

- **Endpoint**: `https://fal.run/fal-ai/glm-image/image-to-image`
- **Model ID**: `fal-ai/glm-image/image-to-image`
- **Category**: image-to-image
- **Kind**: inference
**Tags**: image-to-image



## Pricing

- **Price**: $0.05 per megapixels

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _required_):
  Text prompt for image generation.
  - Examples: "Make the dress red."

- **`image_size`** (`ImageSize | Enum`, _optional_):
  Output image size. Default value: `square_hd`
  - Default: `"square_hd"`
  - One of: ImageSize | Enum

- **`num_inference_steps`** (`integer`, _optional_):
  Number of diffusion denoising steps. More steps generally produce higher quality images. Default value: `30`
  - Default: `30`
  - Range: `10` to `100`

- **`guidance_scale`** (`float`, _optional_):
  Classifier-free guidance scale. Higher values make the model follow the prompt more closely. Default value: `1.5`
  - Default: `1.5`
  - Range: `1` to `10`

- **`seed`** (`integer`, _optional_):
  Random seed for reproducibility. The same seed with the same prompt will produce the same image.

- **`num_images`** (`integer`, _optional_):
  Number of images to generate. Default value: `1`
  - Default: `1`
  - Range: `1` to `4`

- **`enable_safety_checker`** (`boolean`, _optional_):
  Enable NSFW safety checking on the generated images. Default value: `true`
  - Default: `true`

- **`output_format`** (`OutputFormatEnum`, _optional_):
  Output image format. Default value: `"jpeg"`
  - Default: `"jpeg"`
  - Options: `"jpeg"`, `"png"`

- **`sync_mode`** (`boolean`, _optional_):
  If True, the image will be returned as a base64 data URI instead of a URL.
  - Default: `false`

- **`enable_prompt_expansion`** (`boolean`, _optional_):
  If True, the prompt will be enhanced using an LLM for more detailed and higher quality results.
  - Default: `false`

- **`image_urls`** (`list<string>`, _required_):
  URL(s) of the condition image(s) for image-to-image generation. Supports up to 4 URLs for multi-image references.
  - Array of string
  - Examples: "https://storage.googleapis.com/falserverless/example_inputs/catwalk.png"



**Required Parameters Example**:

```json
{
  "prompt": "Make the dress red.",
  "image_urls": "https://storage.googleapis.com/falserverless/example_inputs/catwalk.png"
}
```

**Full Example**:

```json
{
  "prompt": "Make the dress red.",
  "image_size": "square_hd",
  "num_inference_steps": 30,
  "guidance_scale": 1.5,
  "num_images": 1,
  "enable_safety_checker": true,
  "output_format": "jpeg",
  "image_urls": "https://storage.googleapis.com/falserverless/example_inputs/catwalk.png"
}
```


### Output Schema

The API returns the following output format:

- **`images`** (`list<Image>`, _required_):
  List of URLs to the generated images.
  - Array of Image
  - Examples: [{"content_type":"image/png","width":1024,"height":1536,"url":"https://storage.googleapis.com/falserverless/example_outputs/catwalk_red.png"}]

- **`timings`** (`Timings`, _required_)

- **`seed`** (`integer`, _required_):
  Seed of the generated Image. It will be the same value of the one passed in the
  input or the randomly generated that was used in case none was passed.

- **`has_nsfw_concepts`** (`list<boolean>`, _required_):
  Whether the generated images contain NSFW concepts.
  - Array of boolean

- **`prompt`** (`string`, _required_):
  The prompt used for generating the image.



**Example Response**:

```json
{
  "images": [
    {
      "content_type": "image/png",
      "width": 1024,
      "height": 1536,
      "url": "https://storage.googleapis.com/falserverless/example_outputs/catwalk_red.png"
    }
  ],
  "prompt": ""
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/glm-image/image-to-image \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "Make the dress red.",
     "image_urls": "https://storage.googleapis.com/falserverless/example_inputs/catwalk.png"
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
    "fal-ai/glm-image/image-to-image",
    arguments={
        "prompt": "Make the dress red.",
        "image_urls": "https://storage.googleapis.com/falserverless/example_inputs/catwalk.png"
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

const result = await fal.subscribe("fal-ai/glm-image/image-to-image", {
  input: {
    prompt: "Make the dress red.",
    image_urls: "https://storage.googleapis.com/falserverless/example_inputs/catwalk.png"
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

- [Model Playground](https://fal.ai/models/fal-ai/glm-image/image-to-image)
- [API Documentation](https://fal.ai/models/fal-ai/glm-image/image-to-image/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/glm-image/image-to-image)

### fal.ai Platform

- [Platform Documentation](https://docs.fal.ai)
- [Python Client](https://docs.fal.ai/clients/python)
- [JavaScript Client](https://docs.fal.ai/clients/javascript)
