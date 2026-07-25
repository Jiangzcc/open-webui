# Wan

> Edit and transform images using text instructions with the WAN 2.7 Pro model for precise, professional-grade image modifications.


## Overview

- **Endpoint**: `https://fal.run/fal-ai/wan/v2.7/pro/edit`
- **Model ID**: `fal-ai/wan/v2.7/pro/edit`
- **Category**: image-to-image
- **Kind**: inference
**Tags**: wan, image-editing, pro



## Pricing

- **Price**: $0.075 per images

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _required_):
  Text prompt describing the desired image edit. Supports Chinese and English.
  - Examples: "Turn image 1 into a watercolor painting."

- **`image_urls`** (`list<string>`, _required_):
  Reference images for editing (1-4 images required). Order matters: reference them as image 1, image 2, image 3, image 4 in the prompt.
  - Array of string
  - Examples: ["https://storage.googleapis.com/falserverless/model_tests/wan/dragon-warrior.jpg"]

- **`negative_prompt`** (`string`, _optional_):
  Content to avoid in the generated image. Max 500 characters. Default value: `""`
  - Default: `""`

- **`image_size`** (`ImageSize | Enum`, _optional_):
  Output image size. Uses fal image size presets or explicit dimensions and is converted to DashScope size format. Default value: `square_hd`
  - Default: `"square_hd"`
  - One of: ImageSize | Enum

- **`num_images`** (`integer`, _optional_):
  Number of images to generate (1-4). Default value: `1`
  - Default: `1`
  - Range: `1` to `4`

- **`enable_prompt_expansion`** (`boolean`, _optional_):
  Enable DashScope prompt expansion. Supported only for image edit mode. Default value: `true`
  - Default: `true`

- **`seed`** (`integer`, _optional_):
  Random seed for reproducibility (0-2147483647).

- **`enable_safety_checker`** (`boolean`, _optional_):
  Enable content moderation for input and output. Default value: `true`
  - Default: `true`

- **`output_format`** (`OutputFormatEnum`, _optional_):
  The format of the generated images. Default value: `"jpeg"`
  - Default: `"jpeg"`
  - Options: `"jpeg"`, `"png"`, `"webp"`



**Required Parameters Example**:

```json
{
  "prompt": "Turn image 1 into a watercolor painting.",
  "image_urls": [
    "https://storage.googleapis.com/falserverless/model_tests/wan/dragon-warrior.jpg"
  ]
}
```

**Full Example**:

```json
{
  "prompt": "Turn image 1 into a watercolor painting.",
  "image_urls": [
    "https://storage.googleapis.com/falserverless/model_tests/wan/dragon-warrior.jpg"
  ],
  "image_size": "square_hd",
  "num_images": 1,
  "enable_prompt_expansion": true,
  "enable_safety_checker": true,
  "output_format": "jpeg"
}
```


### Output Schema

The API returns the following output format:

- **`images`** (`list<File>`, _required_):
  Generated images.
  - Array of File

- **`seed`** (`integer`, _required_):
  The seed used for generation.



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
  ]
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/wan/v2.7/pro/edit \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "Turn image 1 into a watercolor painting.",
     "image_urls": [
       "https://storage.googleapis.com/falserverless/model_tests/wan/dragon-warrior.jpg"
     ]
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
    "fal-ai/wan/v2.7/pro/edit",
    arguments={
        "prompt": "Turn image 1 into a watercolor painting.",
        "image_urls": ["https://storage.googleapis.com/falserverless/model_tests/wan/dragon-warrior.jpg"]
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

const result = await fal.subscribe("fal-ai/wan/v2.7/pro/edit", {
  input: {
    prompt: "Turn image 1 into a watercolor painting.",
    image_urls: ["https://storage.googleapis.com/falserverless/model_tests/wan/dragon-warrior.jpg"]
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

- [Model Playground](https://fal.ai/models/fal-ai/wan/v2.7/pro/edit)
- [API Documentation](https://fal.ai/models/fal-ai/wan/v2.7/pro/edit/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/wan/v2.7/pro/edit)

### fal.ai Platform

- [Platform Documentation](https://docs.fal.ai)
- [Python Client](https://docs.fal.ai/clients/python)
- [JavaScript Client](https://docs.fal.ai/clients/javascript)
