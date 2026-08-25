# Hunyuan Image

> Leverage the state-of-the-art capabilities of Hunyuan Image 3.0 to generate visual content that effectively conveys the messaging of your written material.


## Overview

- **Endpoint**: `https://fal.run/fal-ai/hunyuan-image/v3/text-to-image`
- **Model ID**: `fal-ai/hunyuan-image/v3/text-to-image`
- **Category**: text-to-image
- **Kind**: inference
**Tags**: text-to-image



## Pricing

- **Price**: $0.1 per megapixels

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _required_):
  The text prompt for image-to-image.
  - Examples: "200mm telephoto through crowd gaps; subject laughing, candid; creamy background compression, color pop from a single bold garment, catchlight in eyes."

- **`negative_prompt`** (`string`, _optional_):
  The negative prompt to guide the image generation away from certain concepts. Default value: `""`
  - Default: `""`
  - Examples: "blurry, low quality, watermark, signature"

- **`image_size`** (`ImageSize | Enum`, _optional_):
  The desired size of the generated image. Default value: `square_hd`
  - Default: `"square_hd"`
  - One of: ImageSize | Enum

- **`num_images`** (`integer`, _optional_):
  The number of images to generate. Default value: `1`
  - Default: `1`
  - Range: `1` to `4`

- **`num_inference_steps`** (`integer`, _optional_):
  Number of denoising steps. Default value: `28`
  - Default: `28`
  - Range: `1` to `50`

- **`guidance_scale`** (`float`, _optional_):
  Controls how much the model adheres to the prompt. Higher values mean stricter adherence. Default value: `7.5`
  - Default: `7.5`
  - Range: `1` to `20`

- **`seed`** (`integer`, _optional_):
  Random seed for reproducible results. If None, a random seed is used.

- **`enable_safety_checker`** (`boolean`, _optional_):
  If set to true, the safety checker will be enabled. Default value: `true`
  - Default: `true`

- **`sync_mode`** (`boolean`, _optional_):
  If `True`, the media will be returned as a data URI and the output data won't be available in the request history.
  - Default: `false`

- **`output_format`** (`OutputFormatEnum`, _optional_):
  The format of the generated image. Default value: `"png"`
  - Default: `"png"`
  - Options: `"jpeg"`, `"png"`

- **`enable_prompt_expansion`** (`boolean`, _optional_):
  Whether to enable prompt expansion. This will use a large language model to expand the prompt with additional details while maintaining the original meaning.
  - Default: `false`
  - Examples: true



**Required Parameters Example**:

```json
{
  "prompt": "200mm telephoto through crowd gaps; subject laughing, candid; creamy background compression, color pop from a single bold garment, catchlight in eyes."
}
```

**Full Example**:

```json
{
  "prompt": "200mm telephoto through crowd gaps; subject laughing, candid; creamy background compression, color pop from a single bold garment, catchlight in eyes.",
  "negative_prompt": "blurry, low quality, watermark, signature",
  "image_size": "square_hd",
  "num_images": 1,
  "num_inference_steps": 28,
  "guidance_scale": 7.5,
  "enable_safety_checker": true,
  "output_format": "png",
  "enable_prompt_expansion": true
}
```


### Output Schema

The API returns the following output format:

- **`images`** (`list<Image>`, _required_):
  A list of the generated images.
  - Array of Image
  - Examples: [{"content_type":"image/png","url":"https://v3b.fal.media/files/b/kangaroo/uIKrZHT6LaGqgXoxtBSn7.png"}]

- **`seed`** (`integer`, _required_):
  The base seed used for the generation process.



**Example Response**:

```json
{
  "images": [
    {
      "content_type": "image/png",
      "url": "https://v3b.fal.media/files/b/kangaroo/uIKrZHT6LaGqgXoxtBSn7.png"
    }
  ]
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/hunyuan-image/v3/text-to-image \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "200mm telephoto through crowd gaps; subject laughing, candid; creamy background compression, color pop from a single bold garment, catchlight in eyes."
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
    "fal-ai/hunyuan-image/v3/text-to-image",
    arguments={
        "prompt": "200mm telephoto through crowd gaps; subject laughing, candid; creamy background compression, color pop from a single bold garment, catchlight in eyes."
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

const result = await fal.subscribe("fal-ai/hunyuan-image/v3/text-to-image", {
  input: {
    prompt: "200mm telephoto through crowd gaps; subject laughing, candid; creamy background compression, color pop from a single bold garment, catchlight in eyes."
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

- [Model Playground](https://fal.ai/models/fal-ai/hunyuan-image/v3/text-to-image)
- [API Documentation](https://fal.ai/models/fal-ai/hunyuan-image/v3/text-to-image/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/hunyuan-image/v3/text-to-image)

### fal.ai Platform

- [Platform Documentation](https://docs.fal.ai)
- [Python Client](https://docs.fal.ai/clients/python)
- [JavaScript Client](https://docs.fal.ai/clients/javascript)
