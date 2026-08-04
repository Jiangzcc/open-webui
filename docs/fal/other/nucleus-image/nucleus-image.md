# Nucleus Image

> Nucleus-Image is a text-to-image generation model built on a sparse mixture-of-experts (MoE) diffusion transformer architecture.


## Overview

- **Endpoint**: `https://fal.run/fal-ai/nucleus-image`
- **Model ID**: `fal-ai/nucleus-image`
- **Category**: text-to-image
- **Kind**: inference
**Tags**: stylized, transform, typography



## Pricing

- **Price**: $0.01 per megapixels

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _required_):
  The prompt to use for generating the image.
  - Examples: "A weathered lighthouse on a rocky coastline at golden hour, waves crashing below, dramatic amber clouds, cinematic realism"

- **`negative_prompt`** (`string`, _optional_):
  The negative prompt to use for generation. Default value: `""`
  - Default: `""`
  - Examples: "blurry, low quality, distorted text"

- **`aspect_ratio`** (`AspectRatioEnum`, _optional_):
  The output aspect ratio. Nucleus-Image supports a fixed set of aspect-ratio presets. Default value: `"1:1"`
  - Default: `"1:1"`
  - Options: `"1:1"`, `"16:9"`, `"9:16"`, `"4:3"`, `"3:4"`, `"3:2"`, `"2:3"`

- **`num_inference_steps`** (`integer`, _optional_):
  The number of inference steps to perform. Default value: `50`
  - Default: `50`
  - Range: `1` to `100`

- **`guidance_scale`** (`float`, _optional_):
  The classifier-free guidance scale. Default value: `8`
  - Default: `8`
  - Range: `0` to `20`

- **`seed`** (`integer`, _optional_):
  Seed for reproducible generation.

- **`num_images`** (`integer`, _optional_):
  The number of images to generate. Default value: `1`
  - Default: `1`
  - Range: `1` to `2`

- **`sync_mode`** (`boolean`, _optional_):
  If `True`, return media as data URIs instead of persisted CDN files.
  - Default: `false`

- **`enable_safety_checker`** (`boolean`, _optional_):
  If set to true, the safety checker will be enabled. Default value: `true`
  - Default: `true`

- **`output_format`** (`OutputFormatEnum`, _optional_):
  The format of the generated image. Default value: `"png"`
  - Default: `"png"`
  - Options: `"jpeg"`, `"png"`



**Required Parameters Example**:

```json
{
  "prompt": "A weathered lighthouse on a rocky coastline at golden hour, waves crashing below, dramatic amber clouds, cinematic realism"
}
```

**Full Example**:

```json
{
  "prompt": "A weathered lighthouse on a rocky coastline at golden hour, waves crashing below, dramatic amber clouds, cinematic realism",
  "negative_prompt": "blurry, low quality, distorted text",
  "aspect_ratio": "1:1",
  "num_inference_steps": 50,
  "guidance_scale": 8,
  "num_images": 1,
  "enable_safety_checker": true,
  "output_format": "png"
}
```


### Output Schema

The API returns the following output format:

- **`images`** (`list<Image>`, _required_):
  The generated image files info.
  - Array of Image

- **`timings`** (`Timings`, _required_)

- **`seed`** (`integer`, _required_):
  Seed of the generated Image. It will be the same value of the one passed in the
  input or the randomly generated that was used in case none was passed.

- **`has_nsfw_concepts`** (`list<boolean>`, _required_):
  Whether the generated images contain NSFW concepts.
  - Array of boolean

- **`prompt`** (`string`, _required_):
  The prompt used for generating the image.



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
  --url https://fal.run/fal-ai/nucleus-image \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "A weathered lighthouse on a rocky coastline at golden hour, waves crashing below, dramatic amber clouds, cinematic realism"
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
    "fal-ai/nucleus-image",
    arguments={
        "prompt": "A weathered lighthouse on a rocky coastline at golden hour, waves crashing below, dramatic amber clouds, cinematic realism"
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

const result = await fal.subscribe("fal-ai/nucleus-image", {
  input: {
    prompt: "A weathered lighthouse on a rocky coastline at golden hour, waves crashing below, dramatic amber clouds, cinematic realism"
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

- [Model Playground](https://fal.ai/models/fal-ai/nucleus-image)
- [API Documentation](https://fal.ai/models/fal-ai/nucleus-image/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/nucleus-image)

### fal.ai Platform

- [Platform Documentation](https://docs.fal.ai)
- [Python Client](https://docs.fal.ai/clients/python)
- [JavaScript Client](https://docs.fal.ai/clients/javascript)
