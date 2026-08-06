# MiniMax (Hailuo AI) Text to Image

> Generate high quality images from text prompts using MiniMax Image-01. Longer text prompts will result in better quality images.


## Overview

- **Endpoint**: `https://fal.run/fal-ai/minimax/image-01`
- **Model ID**: `fal-ai/minimax/image-01`
- **Category**: text-to-image
- **Kind**: inference
**Tags**: stylized, realism



## Pricing

For **1 image** your request will cost **0.01$**. For $1 you can run this model approximately **100** times.

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _required_):
  Text prompt for image generation (max 1500 characters)
  - Examples: "Man dressed in white t shirt, full-body stand front view image, outdoor, Venice beach sign, full-body image, Los Angeles, Fashion photography of 90s, documentary, Film grain, photorealistic"

- **`aspect_ratio`** (`AspectRatioEnum`, _optional_):
  Aspect ratio of the generated image Default value: `"1:1"`
  - Default: `"1:1"`
  - Options: `"1:1"`, `"16:9"`, `"4:3"`, `"3:2"`, `"2:3"`, `"3:4"`, `"9:16"`, `"21:9"`

- **`num_images`** (`integer`, _optional_):
  Number of images to generate (1-9) Default value: `1`
  - Default: `1`
  - Range: `1` to `9`

- **`prompt_optimizer`** (`boolean`, _optional_):
  Whether to enable automatic prompt optimization
  - Default: `false`



**Required Parameters Example**:

```json
{
  "prompt": "Man dressed in white t shirt, full-body stand front view image, outdoor, Venice beach sign, full-body image, Los Angeles, Fashion photography of 90s, documentary, Film grain, photorealistic"
}
```

**Full Example**:

```json
{
  "prompt": "Man dressed in white t shirt, full-body stand front view image, outdoor, Venice beach sign, full-body image, Los Angeles, Fashion photography of 90s, documentary, Film grain, photorealistic",
  "aspect_ratio": "1:1",
  "num_images": 1
}
```


### Output Schema

The API returns the following output format:

- **`images`** (`list<File>`, _required_):
  Generated images
  - Array of File
  - Examples: [{"content_type":"image/jpeg","file_size":351366,"file_name":"image.jpg","url":"https://v3.fal.media/files/tiger/xLcblZAbiw1kM6ZR_2D-r_image.jpg"}]



**Example Response**:

```json
{
  "images": [
    {
      "content_type": "image/jpeg",
      "file_size": 351366,
      "file_name": "image.jpg",
      "url": "https://v3.fal.media/files/tiger/xLcblZAbiw1kM6ZR_2D-r_image.jpg"
    }
  ]
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/minimax/image-01 \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "Man dressed in white t shirt, full-body stand front view image, outdoor, Venice beach sign, full-body image, Los Angeles, Fashion photography of 90s, documentary, Film grain, photorealistic"
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
    "fal-ai/minimax/image-01",
    arguments={
        "prompt": "Man dressed in white t shirt, full-body stand front view image, outdoor, Venice beach sign, full-body image, Los Angeles, Fashion photography of 90s, documentary, Film grain, photorealistic"
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

const result = await fal.subscribe("fal-ai/minimax/image-01", {
  input: {
    prompt: "Man dressed in white t shirt, full-body stand front view image, outdoor, Venice beach sign, full-body image, Los Angeles, Fashion photography of 90s, documentary, Film grain, photorealistic"
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

- [Model Playground](https://fal.ai/models/fal-ai/minimax/image-01)
- [API Documentation](https://fal.ai/models/fal-ai/minimax/image-01/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/minimax/image-01)

### fal.ai Platform

- [Platform Documentation](https://docs.fal.ai)
- [Python Client](https://docs.fal.ai/clients/python)
- [JavaScript Client](https://docs.fal.ai/clients/javascript)
