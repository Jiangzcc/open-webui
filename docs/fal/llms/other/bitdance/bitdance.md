# Bitdance

> Image generation with BitDance. Fast, high-resolution photorealistic images using an autoregressive LLM— for efficient, high-quality results.


## Overview

- **Endpoint**: `https://fal.run/fal-ai/bitdance`
- **Model ID**: `fal-ai/bitdance`
- **Category**: text-to-image
- **Kind**: inference
**Tags**: text-to-image



## Pricing

You will be charged **$0.01** per image generated.

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _required_):
  Text prompt for image generation.
  - Examples: "A close-up portrait of a cat wearing a tiny top hat, cinematic photography style"

- **`image_size`** (`ImageSize | Enum`, _optional_):
  The size of the generated image. Will be snapped to the nearest supported resolution. Default value: `square_hd`
  - Default: `"square_hd"`
  - One of: ImageSize | Enum

- **`num_inference_steps`** (`integer`, _optional_):
  Number of diffusion sampling steps per decoding step. Higher values (e.g. 50) improve quality at the cost of speed. Default value: `25`
  - Default: `25`
  - Range: `10` to `100`

- **`guidance_scale`** (`float`, _optional_):
  Classifier-free guidance scale. Higher values follow the prompt more closely. Default value: `7.5`
  - Default: `7.5`
  - Range: `1` to `15`

- **`seed`** (`integer`, _optional_):
  Random seed for reproducibility. The same seed and prompt will produce the same image.

- **`num_images`** (`integer`, _optional_):
  Number of images to generate. Default value: `1`
  - Default: `1`
  - Range: `1` to `4`

- **`enable_safety_checker`** (`boolean`, _optional_):
  If set to true, the safety checker will be enabled. Default value: `true`
  - Default: `true`

- **`output_format`** (`OutputFormatEnum`, _optional_):
  The format of the generated image. Default value: `"jpeg"`
  - Default: `"jpeg"`
  - Options: `"jpeg"`, `"png"`

- **`sync_mode`** (`boolean`, _optional_):
  If true, the media will be returned as a data URI.
  - Default: `false`



**Required Parameters Example**:

```json
{
  "prompt": "A close-up portrait of a cat wearing a tiny top hat, cinematic photography style"
}
```

**Full Example**:

```json
{
  "prompt": "A close-up portrait of a cat wearing a tiny top hat, cinematic photography style",
  "image_size": "square_hd",
  "num_inference_steps": 25,
  "guidance_scale": 7.5,
  "num_images": 1,
  "enable_safety_checker": true,
  "output_format": "jpeg"
}
```


### Output Schema

The API returns the following output format:

- **`images`** (`list<Image>`, _required_):
  The generated image files info.
  - Array of Image
  - Examples: [{"content_type":"image/jpeg","width":1024,"height":1024,"url":"https://v3b.fal.media/files/b/0a8f4d70/JxZtUW5HcyjcZAEOSzJEl.jpg"}]

- **`seed`** (`integer`, _required_):
  Seed of the generated image.

- **`has_nsfw_concepts`** (`list<boolean>`, _required_):
  Whether the generated images contain NSFW concepts.
  - Array of boolean

- **`prompt`** (`string`, _required_):
  The prompt used for generating the image.
  - Examples: "A close-up portrait of a cat wearing a tiny top hat, cinematic photography style"



**Example Response**:

```json
{
  "images": [
    {
      "content_type": "image/jpeg",
      "width": 1024,
      "height": 1024,
      "url": "https://v3b.fal.media/files/b/0a8f4d70/JxZtUW5HcyjcZAEOSzJEl.jpg"
    }
  ],
  "prompt": "A close-up portrait of a cat wearing a tiny top hat, cinematic photography style"
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/bitdance \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "A close-up portrait of a cat wearing a tiny top hat, cinematic photography style"
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
    "fal-ai/bitdance",
    arguments={
        "prompt": "A close-up portrait of a cat wearing a tiny top hat, cinematic photography style"
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

const result = await fal.subscribe("fal-ai/bitdance", {
  input: {
    prompt: "A close-up portrait of a cat wearing a tiny top hat, cinematic photography style"
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

- [Model Playground](https://fal.ai/models/fal-ai/bitdance)
- [API Documentation](https://fal.ai/models/fal-ai/bitdance/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/bitdance)

### fal.ai Platform

- [Platform Documentation](https://docs.fal.ai)
- [Python Client](https://docs.fal.ai/clients/python)
- [JavaScript Client](https://docs.fal.ai/clients/javascript)
