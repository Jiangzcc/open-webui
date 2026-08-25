# gpt-image-1

> OpenAI's latest image generation and editing model: gpt-1-image.


## Overview

- **Endpoint**: `https://fal.run/fal-ai/gpt-image-1/text-to-image`
- **Model ID**: `fal-ai/gpt-image-1/text-to-image`
- **Category**: text-to-image
- **Kind**: inference


## Pricing

Your request will cost different amounts based on the input and output.
- You will be charged $0.002 per 1,000 input text tokens. One word is roughly 4 tokens.
- For **low** quality, you will be charged $0.011 for 1024x1024 or $0.016 for any other size *per output image*. 
- For **medium** quality, you will be charged $0.042 for 1024x1024 or $0.063 for any other size *per output image*.
- For **high** quality, you will be charged $0.167 for 1024x1024 or $0.25 for any other size *per output image*.
- Your total request cost will be rounded up to the nearest cent.

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _required_):
  The prompt for image generation
  - Examples: "A serene cyberpunk cityscape at twilight, with neon signs glowing in vibrant blues and purples, reflecting on rain-slick streets. Sleek futuristic buildings tower above, connected by glowing skybridges. A lone figure in a hooded jacket stands under a streetlamp, backlit by soft mist. The atmosphere is cinematic, moody"

- **`image_size`** (`ImageSizeEnum`, _optional_):
  Aspect ratio for the generated image Default value: `"auto"`
  - Default: `"auto"`
  - Options: `"auto"`, `"1024x1024"`, `"1536x1024"`, `"1024x1536"`

- **`background`** (`BackgroundEnum`, _optional_):
  Background for the generated image Default value: `"auto"`
  - Default: `"auto"`
  - Options: `"auto"`, `"transparent"`, `"opaque"`

- **`quality`** (`QualityEnum`, _optional_):
  Quality for the generated image Default value: `"auto"`
  - Default: `"auto"`
  - Options: `"auto"`, `"low"`, `"medium"`, `"high"`

- **`num_images`** (`integer`, _optional_):
  Number of images to generate Default value: `1`
  - Default: `1`
  - Range: `1` to `4`
  - Examples: 1

- **`output_format`** (`OutputFormatEnum`, _optional_):
  Output format for the images Default value: `"png"`
  - Default: `"png"`
  - Options: `"jpeg"`, `"png"`, `"webp"`

- **`sync_mode`** (`boolean`, _optional_):
  If `True`, the media will be returned as a data URI and the output data won't be available in the request history.
  - Default: `false`



**Required Parameters Example**:

```json
{
  "prompt": "A serene cyberpunk cityscape at twilight, with neon signs glowing in vibrant blues and purples, reflecting on rain-slick streets. Sleek futuristic buildings tower above, connected by glowing skybridges. A lone figure in a hooded jacket stands under a streetlamp, backlit by soft mist. The atmosphere is cinematic, moody"
}
```

**Full Example**:

```json
{
  "prompt": "A serene cyberpunk cityscape at twilight, with neon signs glowing in vibrant blues and purples, reflecting on rain-slick streets. Sleek futuristic buildings tower above, connected by glowing skybridges. A lone figure in a hooded jacket stands under a streetlamp, backlit by soft mist. The atmosphere is cinematic, moody",
  "image_size": "auto",
  "background": "auto",
  "quality": "auto",
  "num_images": 1,
  "output_format": "png"
}
```


### Output Schema

The API returns the following output format:

- **`images`** (`list<ImageFile>`, _required_):
  The generated images.
  - Array of ImageFile
  - Examples: [{"url":"https://storage.googleapis.com/falserverless/model_tests/gpt-image-1/cyberpunk.png","height":1536,"width":1024,"file_name":"cyberpunk.png","content_type":"image/png"}]



**Example Response**:

```json
{
  "images": [
    {
      "url": "https://storage.googleapis.com/falserverless/model_tests/gpt-image-1/cyberpunk.png",
      "height": 1536,
      "width": 1024,
      "file_name": "cyberpunk.png",
      "content_type": "image/png"
    }
  ]
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/gpt-image-1/text-to-image \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "A serene cyberpunk cityscape at twilight, with neon signs glowing in vibrant blues and purples, reflecting on rain-slick streets. Sleek futuristic buildings tower above, connected by glowing skybridges. A lone figure in a hooded jacket stands under a streetlamp, backlit by soft mist. The atmosphere is cinematic, moody"
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
    "fal-ai/gpt-image-1/text-to-image",
    arguments={
        "prompt": "A serene cyberpunk cityscape at twilight, with neon signs glowing in vibrant blues and purples, reflecting on rain-slick streets. Sleek futuristic buildings tower above, connected by glowing skybridges. A lone figure in a hooded jacket stands under a streetlamp, backlit by soft mist. The atmosphere is cinematic, moody"
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

const result = await fal.subscribe("fal-ai/gpt-image-1/text-to-image", {
  input: {
    prompt: "A serene cyberpunk cityscape at twilight, with neon signs glowing in vibrant blues and purples, reflecting on rain-slick streets. Sleek futuristic buildings tower above, connected by glowing skybridges. A lone figure in a hooded jacket stands under a streetlamp, backlit by soft mist. The atmosphere is cinematic, moody"
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

- [Model Playground](https://fal.ai/models/fal-ai/gpt-image-1/text-to-image)
- [API Documentation](https://fal.ai/models/fal-ai/gpt-image-1/text-to-image/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/gpt-image-1/text-to-image)

### fal.ai Platform

- [Platform Documentation](https://docs.fal.ai)
- [Python Client](https://docs.fal.ai/clients/python)
- [JavaScript Client](https://docs.fal.ai/clients/javascript)
