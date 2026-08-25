# Wan

> Generate high-quality images from text prompts using the WAN 2.7 model with advanced prompt understanding and detailed output.


## Overview

- **Endpoint**: `https://fal.run/fal-ai/wan/v2.7/text-to-image`
- **Model ID**: `fal-ai/wan/v2.7/text-to-image`
- **Category**: text-to-image
- **Kind**: inference
**Tags**: wan, text-to-image, image-generation



## Pricing

- **Price**: $0.03 per images

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _required_):
  Text prompt describing the desired output. Supports Chinese and English.
  - Examples: "An astronaut riding a horse in a photorealistic style."

- **`negative_prompt`** (`string`, _optional_):
  Content to avoid in the generated image. Max 500 characters. Default value: `""`
  - Default: `""`

- **`image_size`** (`ImageSize | Enum`, _optional_):
  Output image size. Default value: `square_hd`
  - Default: `"square_hd"`
  - One of: ImageSize | Enum

- **`num_images`** (`integer`, _optional_):
  Number of images to generate (1-5). Default value: `1`
  - Default: `1`
  - Range: `1` to `5`

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
  "prompt": "An astronaut riding a horse in a photorealistic style."
}
```

**Full Example**:

```json
{
  "prompt": "An astronaut riding a horse in a photorealistic style.",
  "image_size": "square_hd",
  "num_images": 1,
  "enable_safety_checker": true,
  "output_format": "jpeg"
}
```


### Output Schema

The API returns the following output format:

- **`images`** (`list<File>`, _required_):
  Generated images.
  - Array of File

- **`generated_text`** (`string`, _optional_):
  Optional generated text returned by the model.

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
  --url https://fal.run/fal-ai/wan/v2.7/text-to-image \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "An astronaut riding a horse in a photorealistic style."
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
    "fal-ai/wan/v2.7/text-to-image",
    arguments={
        "prompt": "An astronaut riding a horse in a photorealistic style."
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

const result = await fal.subscribe("fal-ai/wan/v2.7/text-to-image", {
  input: {
    prompt: "An astronaut riding a horse in a photorealistic style."
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

- [Model Playground](https://fal.ai/models/fal-ai/wan/v2.7/text-to-image)
- [API Documentation](https://fal.ai/models/fal-ai/wan/v2.7/text-to-image/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/wan/v2.7/text-to-image)

### fal.ai Platform

- [Platform Documentation](https://docs.fal.ai)
- [Python Client](https://docs.fal.ai/clients/python)
- [JavaScript Client](https://docs.fal.ai/clients/javascript)
