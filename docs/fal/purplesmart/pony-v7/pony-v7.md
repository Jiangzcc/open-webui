# Pony V7

> Pony V7 is a finetuned text to image for superior aesthetics and prompt following.


## Overview

- **Endpoint**: `https://fal.run/fal-ai/pony-v7`
- **Model ID**: `fal-ai/pony-v7`
- **Category**: text-to-image
- **Kind**: inference
**Tags**: diffusion, style



## Pricing

- **Price**: $0.03 per megapixels

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _required_):
  The prompt to generate images from
  - Examples: "Close-up portrait of a majestic iguana with vibrant blue-green scales, piercing amber eyes, and orange spiky crest. Intricate textures and details visible on scaly skin. Wrapped in dark hood, giving regal appearance. Dramatic lighting against black background. Hyper-realistic, high-resolution image showcasing the reptile's expressive features and coloration."

- **`image_size`** (`ImageSize | Enum`, _optional_):
  The size of the generated image. Default value: `square_hd`
  - Default: `"square_hd"`
  - One of: ImageSize | Enum

- **`num_images`** (`integer`, _optional_):
  The number of images to generate Default value: `1`
  - Default: `1`
  - Range: `1` to `2`

- **`seed`** (`integer`, _optional_):
  The seed to use for generating images

- **`guidance_scale`** (`float`, _optional_):
  Classifier free guidance scale Default value: `3.5`
  - Default: `3.5`
  - Range: `0` to `20`

- **`num_inference_steps`** (`integer`, _optional_):
  The number of inference steps to take Default value: `40`
  - Default: `40`
  - Range: `20` to `50`

- **`noise_source`** (`NoiseSourceEnum`, _optional_):
  The source of the noise to use for generating images.
  If set to 'gpu', the noise will be generated on the GPU.
  If set to 'cpu', the noise will be generated on the CPU. Default value: `"gpu"`
  - Default: `"gpu"`
  - Options: `"gpu"`, `"cpu"`

- **`sync_mode`** (`boolean`, _optional_):
  If `True`, the media will be returned as a data URI and the output data won't be available in the request history.
  - Default: `false`

- **`enable_safety_checker`** (`boolean`, _optional_):
  If set to true, the safety checker will be enabled.
  - Default: `false`
  - Examples: true

- **`output_format`** (`OutputFormatEnum`, _optional_):
  The format of the generated image. Default value: `"jpeg"`
  - Default: `"jpeg"`
  - Options: `"jpeg"`, `"png"`



**Required Parameters Example**:

```json
{
  "prompt": "Close-up portrait of a majestic iguana with vibrant blue-green scales, piercing amber eyes, and orange spiky crest. Intricate textures and details visible on scaly skin. Wrapped in dark hood, giving regal appearance. Dramatic lighting against black background. Hyper-realistic, high-resolution image showcasing the reptile's expressive features and coloration."
}
```

**Full Example**:

```json
{
  "prompt": "Close-up portrait of a majestic iguana with vibrant blue-green scales, piercing amber eyes, and orange spiky crest. Intricate textures and details visible on scaly skin. Wrapped in dark hood, giving regal appearance. Dramatic lighting against black background. Hyper-realistic, high-resolution image showcasing the reptile's expressive features and coloration.",
  "image_size": "square_hd",
  "num_images": 1,
  "guidance_scale": 3.5,
  "num_inference_steps": 40,
  "noise_source": "gpu",
  "enable_safety_checker": true,
  "output_format": "jpeg"
}
```


### Output Schema

The API returns the following output format:

- **`images`** (`list<Image>`, _required_):
  The generated images
  - Array of Image
  - Examples: [{"url":"https://v3.fal.media/files/monkey/cfJDLaR5mCnlbfoEWXZhm.jpeg","height":1024,"content_type":"image/jpeg","width":1024}]

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
      "url": "https://v3.fal.media/files/monkey/cfJDLaR5mCnlbfoEWXZhm.jpeg",
      "height": 1024,
      "content_type": "image/jpeg",
      "width": 1024
    }
  ],
  "prompt": ""
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/pony-v7 \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "Close-up portrait of a majestic iguana with vibrant blue-green scales, piercing amber eyes, and orange spiky crest. Intricate textures and details visible on scaly skin. Wrapped in dark hood, giving regal appearance. Dramatic lighting against black background. Hyper-realistic, high-resolution image showcasing the reptile's expressive features and coloration."
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
    "fal-ai/pony-v7",
    arguments={
        "prompt": "Close-up portrait of a majestic iguana with vibrant blue-green scales, piercing amber eyes, and orange spiky crest. Intricate textures and details visible on scaly skin. Wrapped in dark hood, giving regal appearance. Dramatic lighting against black background. Hyper-realistic, high-resolution image showcasing the reptile's expressive features and coloration."
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

const result = await fal.subscribe("fal-ai/pony-v7", {
  input: {
    prompt: "Close-up portrait of a majestic iguana with vibrant blue-green scales, piercing amber eyes, and orange spiky crest. Intricate textures and details visible on scaly skin. Wrapped in dark hood, giving regal appearance. Dramatic lighting against black background. Hyper-realistic, high-resolution image showcasing the reptile's expressive features and coloration."
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

- [Model Playground](https://fal.ai/models/fal-ai/pony-v7)
- [API Documentation](https://fal.ai/models/fal-ai/pony-v7/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/pony-v7)

### fal.ai Platform

- [Platform Documentation](https://docs.fal.ai)
- [Python Client](https://docs.fal.ai/clients/python)
- [JavaScript Client](https://docs.fal.ai/clients/javascript)
