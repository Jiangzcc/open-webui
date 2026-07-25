# Qwen Image 2

> Qwen-Image-2.0 is a next-generation foundational unified generation-and-editing model


## Overview

- **Endpoint**: `https://fal.run/fal-ai/qwen-image-2/text-to-image`
- **Model ID**: `fal-ai/qwen-image-2/text-to-image`
- **Category**: text-to-image
- **Kind**: inference
**Tags**: realism, typography



## Pricing

- **Price**: $0.035 per images

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _required_):
  Text prompt describing the desired image. Supports Chinese and English.
  - Examples: "A cute baby koala holding a card says 'Qwen Image 2 is now available on fal' while on a water slider"

- **`negative_prompt`** (`string`, _optional_):
  Content to avoid in the generated image. Max 500 characters. Default value: `""`
  - Default: `""`
  - Examples: "low resolution, error, worst quality, low quality, deformed"

- **`image_size`** (`ImageSize | Enum`, _optional_):
  The size of the generated image. Total number of pixels must be between 512x512 and 2048x2048. Default value: `square_hd`
  - Default: `"square_hd"`
  - One of: ImageSize | Enum
  - Examples: {"width":2048,"height":2048}

- **`enable_prompt_expansion`** (`boolean`, _optional_):
  Enable LLM prompt optimization for better results. Default value: `true`
  - Default: `true`

- **`seed`** (`integer`, _optional_):
  Random seed for reproducibility (0-2147483647).

- **`enable_safety_checker`** (`boolean`, _optional_):
  Enable content moderation for input and output. Default value: `true`
  - Default: `true`

- **`sync_mode`** (`boolean`, _optional_):
  If `True`, the media will be returned as a data URI and the output data won't be available in the request history.
  - Default: `false`

- **`num_images`** (`integer`, _optional_):
  The number of images to generate. Default value: `1`
  - Default: `1`
  - Range: `1` to `4`

- **`output_format`** (`OutputFormatEnum`, _optional_):
  The format of the generated image. Default value: `"png"`
  - Default: `"png"`
  - Options: `"jpeg"`, `"png"`, `"webp"`



**Required Parameters Example**:

```json
{
  "prompt": "A cute baby koala holding a card says 'Qwen Image 2 is now available on fal' while on a water slider"
}
```

**Full Example**:

```json
{
  "prompt": "A cute baby koala holding a card says 'Qwen Image 2 is now available on fal' while on a water slider",
  "negative_prompt": "low resolution, error, worst quality, low quality, deformed",
  "image_size": {
    "width": 2048,
    "height": 2048
  },
  "enable_prompt_expansion": true,
  "enable_safety_checker": true,
  "num_images": 1,
  "output_format": "png"
}
```


### Output Schema

The API returns the following output format:

- **`images`** (`list<File>`, _required_):
  Generated images.
  - Array of File
  - Examples: [{"url":"https://v3b.fal.media/files/b/0a90b32f/SuH1rqlI4Us26LffsOWyV_4HJ5a5RO.png"}]

- **`seed`** (`integer`, _required_):
  The seed used for generation
  - Examples: 42



**Example Response**:

```json
{
  "images": [
    {
      "url": "https://v3b.fal.media/files/b/0a90b32f/SuH1rqlI4Us26LffsOWyV_4HJ5a5RO.png"
    }
  ],
  "seed": 42
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/qwen-image-2/text-to-image \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "A cute baby koala holding a card says 'Qwen Image 2 is now available on fal' while on a water slider"
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
    "fal-ai/qwen-image-2/text-to-image",
    arguments={
        "prompt": "A cute baby koala holding a card says 'Qwen Image 2 is now available on fal' while on a water slider"
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

const result = await fal.subscribe("fal-ai/qwen-image-2/text-to-image", {
  input: {
    prompt: "A cute baby koala holding a card says 'Qwen Image 2 is now available on fal' while on a water slider"
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

- [Model Playground](https://fal.ai/models/fal-ai/qwen-image-2/text-to-image)
- [API Documentation](https://fal.ai/models/fal-ai/qwen-image-2/text-to-image/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/qwen-image-2/text-to-image)

### fal.ai Platform

- [Platform Documentation](https://docs.fal.ai)
- [Python Client](https://docs.fal.ai/clients/python)
- [JavaScript Client](https://docs.fal.ai/clients/javascript)
