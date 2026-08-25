# GPT Image 1 Mini

> GPT Image 1 mini combines OpenAI's advanced language capabilities, powered by GPT-5, with GPT Image 1 Mini for efficient image generation. 


## Overview

- **Endpoint**: `https://fal.run/fal-ai/gpt-image-1-mini`
- **Model ID**: `fal-ai/gpt-image-1-mini`
- **Category**: text-to-image
- **Kind**: inference
**Tags**: text-to-image



## Pricing

Your request will cost different amounts based on the input and output.
- You will be charged $0.002 per 1,000 input text tokens. One word is roughly 4 tokens.
- For **low** quality, you will be charged $0.005 for 1024x1024 or $0.006 for any other size *per output image*. 
- For **medium** quality, you will be charged $0.011 for 1024x1024 or $0.015 for any other size *per output image*.
- For **high** quality, you will be charged $0.036 for 1024x1024 or $0.052 for any other size *per output image*.
- Your total request price will be rounded up to the nearest cent.

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _required_):
  The prompt for image generation
  - Examples: "A serene landscape with mountains reflecting in a crystal-clear lake at sunset, photorealistic style"

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
  "prompt": "A serene landscape with mountains reflecting in a crystal-clear lake at sunset, photorealistic style"
}
```

**Full Example**:

```json
{
  "prompt": "A serene landscape with mountains reflecting in a crystal-clear lake at sunset, photorealistic style",
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
  - Examples: [{"content_type":"image/jpeg","file_name":"1EXVSVlSs4Yz5hKplrzTv_2595c4e8720f4c19bcbc3dd373b18065.jpg","width":1024,"height":1024,"url":"https://v3b.fal.media/files/b/elephant/1EXVSVlSs4Yz5hKplrzTv_2595c4e8720f4c19bcbc3dd373b18065.jpg"}]



**Example Response**:

```json
{
  "images": [
    {
      "content_type": "image/jpeg",
      "file_name": "1EXVSVlSs4Yz5hKplrzTv_2595c4e8720f4c19bcbc3dd373b18065.jpg",
      "width": 1024,
      "height": 1024,
      "url": "https://v3b.fal.media/files/b/elephant/1EXVSVlSs4Yz5hKplrzTv_2595c4e8720f4c19bcbc3dd373b18065.jpg"
    }
  ]
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/gpt-image-1-mini \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "A serene landscape with mountains reflecting in a crystal-clear lake at sunset, photorealistic style"
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
    "fal-ai/gpt-image-1-mini",
    arguments={
        "prompt": "A serene landscape with mountains reflecting in a crystal-clear lake at sunset, photorealistic style"
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

const result = await fal.subscribe("fal-ai/gpt-image-1-mini", {
  input: {
    prompt: "A serene landscape with mountains reflecting in a crystal-clear lake at sunset, photorealistic style"
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

- [Model Playground](https://fal.ai/models/fal-ai/gpt-image-1-mini)
- [API Documentation](https://fal.ai/models/fal-ai/gpt-image-1-mini/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/gpt-image-1-mini)

### fal.ai Platform

- [Platform Documentation](https://docs.fal.ai)
- [Python Client](https://docs.fal.ai/clients/python)
- [JavaScript Client](https://docs.fal.ai/clients/javascript)
