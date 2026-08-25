# Ideogram V2 Edit

> Transform existing images with Ideogram V2's editing capabilities. Modify, adjust, and refine images while maintaining high fidelity and realistic outputs with precise prompt control.


## Overview

- **Endpoint**: `https://fal.run/fal-ai/ideogram/v2/edit`
- **Model ID**: `fal-ai/ideogram/v2/edit`
- **Category**: image-to-image
- **Kind**: inference
**Tags**: realism, typography



## Pricing

- **Price**: $0.08 per images

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _required_):
  The prompt to fill the masked part of the image.
  - Examples: "A knight in shining armour holding a greatshield with \"FAL\" on it"

- **`image_url`** (`string`, _required_):
  The image URL to generate an image from. Needs to match the dimensions of the mask.
  - Examples: "https://storage.googleapis.com/falserverless/flux-lora/example-images/knight.jpeg"

- **`mask_url`** (`string`, _required_):
  The mask URL to inpaint the image. Needs to match the dimensions of the input image.
  - Examples: "https://storage.googleapis.com/falserverless/flux-lora/example-images/mask_knight.jpeg"

- **`seed`** (`integer`, _optional_):
  Seed for the random number generator

- **`style`** (`StyleEnum`, _optional_):
  The style of the generated image Default value: `"auto"`
  - Default: `"auto"`
  - Options: `"auto"`, `"general"`, `"realistic"`, `"design"`, `"render_3D"`, `"anime"`

- **`expand_prompt`** (`boolean`, _optional_):
  Whether to expand the prompt with MagicPrompt functionality. Default value: `true`
  - Default: `true`

- **`sync_mode`** (`boolean`, _optional_):
  If `True`, the media will be returned as a data URI and the output data won't be available in the request history.
  - Default: `false`



**Required Parameters Example**:

```json
{
  "prompt": "A knight in shining armour holding a greatshield with \"FAL\" on it",
  "image_url": "https://storage.googleapis.com/falserverless/flux-lora/example-images/knight.jpeg",
  "mask_url": "https://storage.googleapis.com/falserverless/flux-lora/example-images/mask_knight.jpeg"
}
```

**Full Example**:

```json
{
  "prompt": "A knight in shining armour holding a greatshield with \"FAL\" on it",
  "image_url": "https://storage.googleapis.com/falserverless/flux-lora/example-images/knight.jpeg",
  "mask_url": "https://storage.googleapis.com/falserverless/flux-lora/example-images/mask_knight.jpeg",
  "style": "auto",
  "expand_prompt": true
}
```


### Output Schema

The API returns the following output format:

- **`images`** (`list<File>`, _required_)
  - Array of File
  - Examples: [{"url":"https://fal.media/files/monkey/cNaoxPl0YAWYb-QVBvO9F_image.png"}]

- **`seed`** (`integer`, _required_):
  Seed used for the random number generator
  - Examples: 123456



**Example Response**:

```json
{
  "images": [
    {
      "url": "https://fal.media/files/monkey/cNaoxPl0YAWYb-QVBvO9F_image.png"
    }
  ],
  "seed": 123456
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/ideogram/v2/edit \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "A knight in shining armour holding a greatshield with \"FAL\" on it",
     "image_url": "https://storage.googleapis.com/falserverless/flux-lora/example-images/knight.jpeg",
     "mask_url": "https://storage.googleapis.com/falserverless/flux-lora/example-images/mask_knight.jpeg"
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
    "fal-ai/ideogram/v2/edit",
    arguments={
        "prompt": "A knight in shining armour holding a greatshield with \"FAL\" on it",
        "image_url": "https://storage.googleapis.com/falserverless/flux-lora/example-images/knight.jpeg",
        "mask_url": "https://storage.googleapis.com/falserverless/flux-lora/example-images/mask_knight.jpeg"
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

const result = await fal.subscribe("fal-ai/ideogram/v2/edit", {
  input: {
    prompt: "A knight in shining armour holding a greatshield with \"FAL\" on it",
    image_url: "https://storage.googleapis.com/falserverless/flux-lora/example-images/knight.jpeg",
    mask_url: "https://storage.googleapis.com/falserverless/flux-lora/example-images/mask_knight.jpeg"
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

- [Model Playground](https://fal.ai/models/fal-ai/ideogram/v2/edit)
- [API Documentation](https://fal.ai/models/fal-ai/ideogram/v2/edit/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/ideogram/v2/edit)

### fal.ai Platform

- [Platform Documentation](https://docs.fal.ai)
- [Python Client](https://docs.fal.ai/clients/python)
- [JavaScript Client](https://docs.fal.ai/clients/javascript)
