# Ernie Image Lora

> High-quality text-to-image model by Baidu. Supports English, Chinese, and Japanese prompts with built-in prompt expansion.


## Overview

- **Endpoint**: `https://fal.run/fal-ai/ernie-image/lora`
- **Model ID**: `fal-ai/ernie-image/lora`
- **Category**: text-to-image
- **Kind**: inference


## Pricing

- **Price**: $0.035 per megapixels

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _required_):
  Text prompt for image generation. Supports English, Chinese, and Japanese.
  - Examples: "A serene mountain landscape at sunset with golden light"

- **`negative_prompt`** (`string`, _optional_):
  Negative prompt to guide what should not be in the image. Default value: `""`
  - Default: `""`

- **`image_size`** (`ImageSize | Enum`, _optional_):
  The size of the generated image. Default value: `square_hd`
  - Default: `"square_hd"`
  - One of: ImageSize | Enum

- **`num_inference_steps`** (`integer`, _optional_):
  Number of denoising steps. Default value: `50`
  - Default: `50`
  - Range: `1` to `100`

- **`guidance_scale`** (`float`, _optional_):
  Classifier-free guidance scale. Default value: `5`
  - Default: `5`
  - Range: `1` to `20`

- **`seed`** (`integer`, _optional_):
  Random seed for reproducibility.

- **`num_images`** (`integer`, _optional_):
  Number of images to generate. Default value: `1`
  - Default: `1`
  - Range: `1` to `4`

- **`enable_prompt_expansion`** (`boolean`, _optional_):
  If True, the prompt will be enhanced using an LLM for more detailed results. Default value: `true`
  - Default: `true`

- **`enable_safety_checker`** (`boolean`, _optional_):
  Enable NSFW safety checking on the generated images. Default value: `true`
  - Default: `true`

- **`output_format`** (`OutputFormatEnum`, _optional_):
  Output image format. Default value: `"jpeg"`
  - Default: `"jpeg"`
  - Options: `"jpeg"`, `"png"`

- **`sync_mode`** (`boolean`, _optional_):
  If True, the image will be returned as a data URI instead of a URL.
  - Default: `false`

- **`acceleration`** (`AccelerationEnum`, _optional_):
  The acceleration level to use for the image generation. Default value: `"regular"`
  - Default: `"regular"`
  - Options: `"none"`, `"regular"`, `"high"`
  - Examples: "regular"

- **`loras`** (`list<LoraWeight>`, _optional_):
  The LoRAs to use for image generation. You can use up to 3 LoRAs and they will be merged together to generate the final image.
  - Default: `[]`
  - Array of LoraWeight



**Required Parameters Example**:

```json
{
  "prompt": "A serene mountain landscape at sunset with golden light"
}
```

**Full Example**:

```json
{
  "prompt": "A serene mountain landscape at sunset with golden light",
  "image_size": "square_hd",
  "num_inference_steps": 50,
  "guidance_scale": 5,
  "num_images": 1,
  "enable_prompt_expansion": true,
  "enable_safety_checker": true,
  "output_format": "jpeg",
  "acceleration": "regular",
  "loras": []
}
```


### Output Schema

The API returns the following output format:

- **`images`** (`list<Image>`, _required_):
  List of generated images.
  - Array of Image

- **`seed`** (`integer`, _required_):
  Seed used for generation.

- **`prompt`** (`string`, _required_):
  The prompt used for generating the image.

- **`timings`** (`Timings`, _required_):
  Timing information.



**Example Response**:

```json
{
  "images": [
    {
      "url": "",
      "content_type": "image/jpeg"
    }
  ],
  "prompt": ""
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/ernie-image/lora \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "A serene mountain landscape at sunset with golden light"
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
    "fal-ai/ernie-image/lora",
    arguments={
        "prompt": "A serene mountain landscape at sunset with golden light"
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

const result = await fal.subscribe("fal-ai/ernie-image/lora", {
  input: {
    prompt: "A serene mountain landscape at sunset with golden light"
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

- [Model Playground](https://fal.ai/models/fal-ai/ernie-image/lora)
- [API Documentation](https://fal.ai/models/fal-ai/ernie-image/lora/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/ernie-image/lora)

### fal.ai Platform

- [Platform Documentation](https://docs.fal.ai)
- [Python Client](https://docs.fal.ai/clients/python)
- [JavaScript Client](https://docs.fal.ai/clients/javascript)
