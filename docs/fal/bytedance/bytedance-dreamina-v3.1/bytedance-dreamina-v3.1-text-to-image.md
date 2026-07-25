# Bytedance Dreamina V3.1 Text To Image

> Dreamina showcases superior picture effects, with significant improvements in picture aesthetics, precise and diverse styles, and rich details.


## Overview

- **Endpoint**: `https://fal.run/fal-ai/bytedance/dreamina/v3.1/text-to-image`
- **Model ID**: `fal-ai/bytedance/dreamina/v3.1/text-to-image`
- **Category**: text-to-image
- **Kind**: inference
**Tags**: text-to-image



## Pricing

- **Price**: $0.03 per images

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _required_):
  The text prompt used to generate the image
  - Examples: "A 25-year-old korean woman selfie, front facing camera, lighting is soft and natural. If background is visible, it's a clean, modern apartment interior. The clothing color is clearly visible and distinct, adding a hint of color contrast"

- **`image_size`** (`ImageSize | Enum`, _optional_):
  The size of the generated image. Width and height must be between 512 and 2048.
  - Default: `{"height":1536,"width":2048}`
  - One of: ImageSize | Enum

- **`enhance_prompt`** (`boolean`, _optional_):
  Whether to use an LLM to enhance the prompt
  - Default: `false`

- **`num_images`** (`integer`, _optional_):
  Number of images to generate Default value: `1`
  - Default: `1`
  - Range: `1` to `4`

- **`seed`** (`integer`, _optional_):
  Random seed to control the stochasticity of image generation.

- **`sync_mode`** (`boolean`, _optional_):
  If `True`, the media will be returned as a data URI and the output data won't be available in the request history.
  - Default: `false`



**Required Parameters Example**:

```json
{
  "prompt": "A 25-year-old korean woman selfie, front facing camera, lighting is soft and natural. If background is visible, it's a clean, modern apartment interior. The clothing color is clearly visible and distinct, adding a hint of color contrast"
}
```

**Full Example**:

```json
{
  "prompt": "A 25-year-old korean woman selfie, front facing camera, lighting is soft and natural. If background is visible, it's a clean, modern apartment interior. The clothing color is clearly visible and distinct, adding a hint of color contrast",
  "image_size": {
    "height": 1536,
    "width": 2048
  },
  "num_images": 1
}
```


### Output Schema

The API returns the following output format:

- **`images`** (`list<Image>`, _required_):
  Generated images
  - Array of Image
  - Examples: [{"url":"https://v3.fal.media/files/panda/4mddd7PmDvbbBZDs-xnUW_4294a9041c9d46eaa7b98d15ce6300fb.png"}]

- **`seed`** (`integer`, _required_):
  Seed used for generation
  - Examples: 746406749



**Example Response**:

```json
{
  "images": [
    {
      "url": "https://v3.fal.media/files/panda/4mddd7PmDvbbBZDs-xnUW_4294a9041c9d46eaa7b98d15ce6300fb.png"
    }
  ],
  "seed": 746406749
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/bytedance/dreamina/v3.1/text-to-image \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "A 25-year-old korean woman selfie, front facing camera, lighting is soft and natural. If background is visible, it's a clean, modern apartment interior. The clothing color is clearly visible and distinct, adding a hint of color contrast"
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
    "fal-ai/bytedance/dreamina/v3.1/text-to-image",
    arguments={
        "prompt": "A 25-year-old korean woman selfie, front facing camera, lighting is soft and natural. If background is visible, it's a clean, modern apartment interior. The clothing color is clearly visible and distinct, adding a hint of color contrast"
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

const result = await fal.subscribe("fal-ai/bytedance/dreamina/v3.1/text-to-image", {
  input: {
    prompt: "A 25-year-old korean woman selfie, front facing camera, lighting is soft and natural. If background is visible, it's a clean, modern apartment interior. The clothing color is clearly visible and distinct, adding a hint of color contrast"
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

- [Model Playground](https://fal.ai/models/fal-ai/bytedance/dreamina/v3.1/text-to-image)
- [API Documentation](https://fal.ai/models/fal-ai/bytedance/dreamina/v3.1/text-to-image/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/bytedance/dreamina/v3.1/text-to-image)

### fal.ai Platform

- [Platform Documentation](https://docs.fal.ai)
- [Python Client](https://docs.fal.ai/clients/python)
- [JavaScript Client](https://docs.fal.ai/clients/javascript)
