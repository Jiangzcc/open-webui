# FLUX.2 [klein] 4B Base

> Image-to-image editing with FLUX.2 [klein] 4B Base from Black Forest Labs. Precise modifications using natural language descriptions and hex color control.


## Overview

- **Endpoint**: `https://fal.run/fal-ai/flux-2/klein/4b/base/edit`
- **Model ID**: `fal-ai/flux-2/klein/4b/base/edit`
- **Category**: image-to-image
- **Kind**: inference


## Pricing

Requests cost **$0.009** per megapixel of input and output. Input images will be resized to 1MP. For example, a 1024×1024 generation with a 512×512 input image will cost **$0.018** (1 MP input + 1 MP output, each costing **$0.009**).

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _required_):
  The prompt to edit the image.
  - Examples: "Imagine view of Fuji mount. Use style of reference image."

- **`negative_prompt`** (`string`, _optional_):
  Negative prompt for classifier-free guidance. Describes what to avoid in the image. Default value: `""`
  - Default: `""`

- **`guidance_scale`** (`float`, _optional_):
  Guidance scale for classifier-free guidance. Default value: `5`
  - Default: `5`
  - Range: `0` to `20`

- **`seed`** (`integer`, _optional_):
  The seed to use for the generation. If not provided, a random seed will be used.

- **`num_inference_steps`** (`integer`, _optional_):
  The number of inference steps to perform. Default value: `28`
  - Default: `28`
  - Range: `4` to `50`

- **`image_size`** (`ImageSize | Enum`, _optional_):
  The size of the generated image. If not provided, uses the input image size.
  - One of: ImageSize | Enum
  - Examples: {"width":2016,"height":1152}

- **`num_images`** (`integer`, _optional_):
  The number of images to generate. Default value: `1`
  - Default: `1`
  - Range: `1` to `4`

- **`acceleration`** (`AccelerationEnum`, _optional_):
  The acceleration level to use for image generation. Default value: `"regular"`
  - Default: `"regular"`
  - Options: `"none"`, `"regular"`, `"high"`

- **`sync_mode`** (`boolean`, _optional_):
  If `True`, the media will be returned as a data URI. Output is not stored when this is True.
  - Default: `false`

- **`enable_safety_checker`** (`boolean`, _optional_):
  If set to true, the safety checker will be enabled. Default value: `true`
  - Default: `true`

- **`output_format`** (`OutputFormatEnum`, _optional_):
  The format of the generated image. Default value: `"png"`
  - Default: `"png"`
  - Options: `"jpeg"`, `"png"`, `"webp"`

- **`image_urls`** (`list<string>`, _required_):
  The URLs of the images for editing. A maximum of 4 images are allowed.
  - Array of string
  - Examples: ["https://v3b.fal.media/files/b/0a8a69fd/VUrxIXgOqcf3L7kuGS7B5_eb54fcdc-87d0-47da-ad31-93455b245fb4.png"]



**Required Parameters Example**:

```json
{
  "prompt": "Imagine view of Fuji mount. Use style of reference image.",
  "image_urls": [
    "https://v3b.fal.media/files/b/0a8a69fd/VUrxIXgOqcf3L7kuGS7B5_eb54fcdc-87d0-47da-ad31-93455b245fb4.png"
  ]
}
```

**Full Example**:

```json
{
  "prompt": "Imagine view of Fuji mount. Use style of reference image.",
  "guidance_scale": 5,
  "num_inference_steps": 28,
  "image_size": {
    "width": 2016,
    "height": 1152
  },
  "num_images": 1,
  "acceleration": "regular",
  "enable_safety_checker": true,
  "output_format": "png",
  "image_urls": [
    "https://v3b.fal.media/files/b/0a8a69fd/VUrxIXgOqcf3L7kuGS7B5_eb54fcdc-87d0-47da-ad31-93455b245fb4.png"
  ]
}
```


### Output Schema

The API returns the following output format:

- **`images`** (`list<ImageFile>`, _required_):
  The edited images
  - Array of ImageFile
  - Examples: [{"url":"https://v3b.fal.media/files/b/0a8a69ff/UYukVfGjybLo7spA_Kc-i.png"}]

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
      "url": "https://v3b.fal.media/files/b/0a8a69ff/UYukVfGjybLo7spA_Kc-i.png"
    }
  ],
  "prompt": ""
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/flux-2/klein/4b/base/edit \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "Imagine view of Fuji mount. Use style of reference image.",
     "image_urls": [
       "https://v3b.fal.media/files/b/0a8a69fd/VUrxIXgOqcf3L7kuGS7B5_eb54fcdc-87d0-47da-ad31-93455b245fb4.png"
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
    "fal-ai/flux-2/klein/4b/base/edit",
    arguments={
        "prompt": "Imagine view of Fuji mount. Use style of reference image.",
        "image_urls": ["https://v3b.fal.media/files/b/0a8a69fd/VUrxIXgOqcf3L7kuGS7B5_eb54fcdc-87d0-47da-ad31-93455b245fb4.png"]
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

const result = await fal.subscribe("fal-ai/flux-2/klein/4b/base/edit", {
  input: {
    prompt: "Imagine view of Fuji mount. Use style of reference image.",
    image_urls: ["https://v3b.fal.media/files/b/0a8a69fd/VUrxIXgOqcf3L7kuGS7B5_eb54fcdc-87d0-47da-ad31-93455b245fb4.png"]
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

- [Model Playground](https://fal.ai/models/fal-ai/flux-2/klein/4b/base/edit)
- [API Documentation](https://fal.ai/models/fal-ai/flux-2/klein/4b/base/edit/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/flux-2/klein/4b/base/edit)

### fal.ai Platform

- [Platform Documentation](https://docs.fal.ai)
- [Python Client](https://docs.fal.ai/clients/python)
- [JavaScript Client](https://docs.fal.ai/clients/javascript)
