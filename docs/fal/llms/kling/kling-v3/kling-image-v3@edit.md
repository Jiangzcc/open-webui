# Kling Image

> Kling Image V3: Latest kling image model


## Overview

- **Endpoint**: `https://fal.run/fal-ai/kling-image/v3/image-to-image`
- **Model ID**: `fal-ai/kling-image/v3/image-to-image`
- **Category**: image-to-image
- **Kind**: inference
**Tags**: image-to-image



## Pricing

- **Price**: $0.028 per images

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _required_):
  Text prompt for image generation. Max 2500 characters.
  - Examples: "Transform to deep winter, heavy snow covering all surfaces, bare frozen trees, overcast sky, footprints in fresh powder, cold blue color grade"

- **`image_url`** (`string`, _required_):
  Reference image for image-to-image generation.
  
  Max file size: 10.0MB, Min width: 300px, Min height: 300px, Min aspect ratio: 0.40, Max aspect ratio: 2.50, Timeout: 20.0s
  - Examples: "https://v3b.fal.media/files/b/0a8d06b9/3zxm2qoj2xYWSNwEe5Vd9_a74d767fc42e47a0bf657117fbcf8b90.png"

- **`elements`** (`list<ElementInput>`, _optional_):
  Optional: Elements (characters/objects) to include in the image for face control.
  - Array of ElementInput

- **`resolution`** (`ResolutionEnum`, _optional_):
  Image generation resolution. 1K: standard, 2K: high-res. Default value: `"1K"`
  - Default: `"1K"`
  - Options: `"1K"`, `"2K"`

- **`num_images`** (`integer`, _optional_):
  Number of images to generate (1-9). Default value: `1`
  - Default: `1`
  - Range: `1` to `9`

- **`aspect_ratio`** (`AspectRatioEnum`, _optional_):
  Aspect ratio of generated images. Default value: `"16:9"`
  - Default: `"16:9"`
  - Options: `"16:9"`, `"9:16"`, `"1:1"`, `"4:3"`, `"3:4"`, `"3:2"`, `"2:3"`, `"21:9"`

- **`output_format`** (`OutputFormatEnum`, _optional_):
  The format of the generated image. Default value: `"png"`
  - Default: `"png"`
  - Options: `"jpeg"`, `"png"`, `"webp"`

- **`sync_mode`** (`boolean`, _optional_):
  If `True`, the media will be returned as a data URI.
  - Default: `false`



**Required Parameters Example**:

```json
{
  "prompt": "Transform to deep winter, heavy snow covering all surfaces, bare frozen trees, overcast sky, footprints in fresh powder, cold blue color grade",
  "image_url": "https://v3b.fal.media/files/b/0a8d06b9/3zxm2qoj2xYWSNwEe5Vd9_a74d767fc42e47a0bf657117fbcf8b90.png"
}
```

**Full Example**:

```json
{
  "prompt": "Transform to deep winter, heavy snow covering all surfaces, bare frozen trees, overcast sky, footprints in fresh powder, cold blue color grade",
  "image_url": "https://v3b.fal.media/files/b/0a8d06b9/3zxm2qoj2xYWSNwEe5Vd9_a74d767fc42e47a0bf657117fbcf8b90.png",
  "elements": [
    {}
  ],
  "resolution": "1K",
  "num_images": 1,
  "aspect_ratio": "16:9",
  "output_format": "png"
}
```


### Output Schema

The API returns the following output format:

- **`images`** (`list<Image>`, _required_):
  Generated images
  - Array of Image
  - Examples: [{"content_type":"image/png","file_size":2085483,"url":"https://v3b.fal.media/files/b/0a8d06c0/PJqs6iVST-NaBlt8uMwVJ_49222c3290cd4cefb3baacac2cb004ce.png","file_name":"49222c3290cd4cefb3baacac2cb004ce.png"}]



**Example Response**:

```json
{
  "images": [
    {
      "content_type": "image/png",
      "file_size": 2085483,
      "url": "https://v3b.fal.media/files/b/0a8d06c0/PJqs6iVST-NaBlt8uMwVJ_49222c3290cd4cefb3baacac2cb004ce.png",
      "file_name": "49222c3290cd4cefb3baacac2cb004ce.png"
    }
  ]
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/kling-image/v3/image-to-image \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "Transform to deep winter, heavy snow covering all surfaces, bare frozen trees, overcast sky, footprints in fresh powder, cold blue color grade",
     "image_url": "https://v3b.fal.media/files/b/0a8d06b9/3zxm2qoj2xYWSNwEe5Vd9_a74d767fc42e47a0bf657117fbcf8b90.png"
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
    "fal-ai/kling-image/v3/image-to-image",
    arguments={
        "prompt": "Transform to deep winter, heavy snow covering all surfaces, bare frozen trees, overcast sky, footprints in fresh powder, cold blue color grade",
        "image_url": "https://v3b.fal.media/files/b/0a8d06b9/3zxm2qoj2xYWSNwEe5Vd9_a74d767fc42e47a0bf657117fbcf8b90.png"
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

const result = await fal.subscribe("fal-ai/kling-image/v3/image-to-image", {
  input: {
    prompt: "Transform to deep winter, heavy snow covering all surfaces, bare frozen trees, overcast sky, footprints in fresh powder, cold blue color grade",
    image_url: "https://v3b.fal.media/files/b/0a8d06b9/3zxm2qoj2xYWSNwEe5Vd9_a74d767fc42e47a0bf657117fbcf8b90.png"
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

- [Model Playground](https://fal.ai/models/fal-ai/kling-image/v3/image-to-image)
- [API Documentation](https://fal.ai/models/fal-ai/kling-image/v3/image-to-image/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/kling-image/v3/image-to-image)

### fal.ai Platform

- [Platform Documentation](https://docs.fal.ai)
- [Python Client](https://docs.fal.ai/clients/python)
- [JavaScript Client](https://docs.fal.ai/clients/javascript)
