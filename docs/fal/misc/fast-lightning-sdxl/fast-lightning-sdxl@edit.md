# Stable Diffusion XL Lightning

> Run SDXL at the speed of light


## Overview

- **Endpoint**: `https://fal.run/fal-ai/fast-lightning-sdxl/image-to-image`
- **Model ID**: `fal-ai/fast-lightning-sdxl/image-to-image`
- **Category**: image-to-image
- **Kind**: inference
**Tags**: diffusion, lightning, editing



## Pricing

- **Price**: $0 per compute seconds

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`image_url`** (`string`, _required_):
  The URL of the image to use as a starting point for the generation.
  - Examples: "https://fal-cdn.batuhan-941.workers.dev/files/tiger/IExuP-WICqaIesLZAZPur.jpeg"

- **`prompt`** (`string`, _required_):
  The prompt to use for generating the image. Be as descriptive as possible for best results.
  - Examples: "an island near sea, with seagulls, moon shining over the sea, light house, boats int he background, fish flying over the sea"

- **`image_size`** (`ImageSize | Enum`, _optional_):
  The size of the generated image. Default value: `square_hd`
  - Default: `"square_hd"`
  - One of: ImageSize | Enum

- **`num_inference_steps`** (`NumInferenceStepsEnum`, _optional_):
  The number of inference steps to perform. Default value: `"4"`
  - Default: `4`
  - Options: `"1"`, `"2"`, `"4"`, `"8"`

- **`strength`** (`float`, _optional_):
  determines how much the generated image resembles the initial image Default value: `0.95`
  - Default: `0.95`
  - Range: `0.05` to `1`

- **`seed`** (`integer`, _optional_):
  The same seed and the same prompt given to the same version of Stable Diffusion
  will output the same image every time.

- **`sync_mode`** (`boolean`, _optional_):
  If `True`, the media will be returned as a data URI and the output data won't be available in the request history.
  - Default: `false`

- **`num_images`** (`integer`, _optional_):
  The number of images to generate. Default value: `1`
  - Default: `1`
  - Range: `1` to `8`

- **`embeddings`** (`list<Embedding>`, _optional_):
  The list of embeddings to use.
  - Default: `[]`
  - Array of Embedding

- **`enable_safety_checker`** (`boolean`, _optional_):
  If set to true, the safety checker will be enabled. Default value: `true`
  - Default: `true`

- **`safety_checker_version`** (`SafetyCheckerVersionEnum`, _optional_):
  The version of the safety checker to use. v1 is the default CompVis safety checker. v2 uses a custom ViT model. Default value: `"v1"`
  - Default: `"v1"`
  - Options: `"v1"`, `"v2"`

- **`expand_prompt`** (`boolean`, _optional_):
  If set to true, the prompt will be expanded with additional prompts.
  - Default: `false`

- **`format`** (`FormatEnum`, _optional_):
  The format of the generated image. Default value: `"jpeg"`
  - Default: `"jpeg"`
  - Options: `"jpeg"`, `"png"`

- **`request_id`** (`string`, _optional_):
  An id bound to a request, can be used with response to identify the request
  itself. Default value: `""`
  - Default: `""`

- **`preserve_aspect_ratio`** (`boolean`, _optional_):
  If set to true, the aspect ratio of the generated image will be preserved even
  if the image size is too large. However, if the image is not a multiple of 32
  in width or height, it will be resized to the nearest multiple of 32. By default,
  this snapping to the nearest multiple of 32 will not preserve the aspect ratio.
  Set crop_output to True, to crop the output to the proper aspect ratio
  after generating.
  - Default: `false`

- **`crop_output`** (`boolean`, _optional_):
  If set to true, the output cropped to the proper aspect ratio after generating.
  - Default: `false`



**Required Parameters Example**:

```json
{
  "image_url": "https://fal-cdn.batuhan-941.workers.dev/files/tiger/IExuP-WICqaIesLZAZPur.jpeg",
  "prompt": "an island near sea, with seagulls, moon shining over the sea, light house, boats int he background, fish flying over the sea"
}
```

**Full Example**:

```json
{
  "image_url": "https://fal-cdn.batuhan-941.workers.dev/files/tiger/IExuP-WICqaIesLZAZPur.jpeg",
  "prompt": "an island near sea, with seagulls, moon shining over the sea, light house, boats int he background, fish flying over the sea",
  "image_size": "square_hd",
  "num_inference_steps": 4,
  "strength": 0.95,
  "num_images": 1,
  "embeddings": [],
  "enable_safety_checker": true,
  "safety_checker_version": "v1",
  "format": "jpeg"
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
  --url https://fal.run/fal-ai/fast-lightning-sdxl/image-to-image \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "image_url": "https://fal-cdn.batuhan-941.workers.dev/files/tiger/IExuP-WICqaIesLZAZPur.jpeg",
     "prompt": "an island near sea, with seagulls, moon shining over the sea, light house, boats int he background, fish flying over the sea"
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
    "fal-ai/fast-lightning-sdxl/image-to-image",
    arguments={
        "image_url": "https://fal-cdn.batuhan-941.workers.dev/files/tiger/IExuP-WICqaIesLZAZPur.jpeg",
        "prompt": "an island near sea, with seagulls, moon shining over the sea, light house, boats int he background, fish flying over the sea"
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

const result = await fal.subscribe("fal-ai/fast-lightning-sdxl/image-to-image", {
  input: {
    image_url: "https://fal-cdn.batuhan-941.workers.dev/files/tiger/IExuP-WICqaIesLZAZPur.jpeg",
    prompt: "an island near sea, with seagulls, moon shining over the sea, light house, boats int he background, fish flying over the sea"
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

- [Model Playground](https://fal.ai/models/fal-ai/fast-lightning-sdxl/image-to-image)
- [API Documentation](https://fal.ai/models/fal-ai/fast-lightning-sdxl/image-to-image/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/fast-lightning-sdxl/image-to-image)
- [GitHub Repository](https://huggingface.co/ByteDance/SDXL-Lightning/blob/main/LICENSE.md)

### fal.ai Platform

- [Platform Documentation](https://docs.fal.ai)
- [Python Client](https://docs.fal.ai/clients/python)
- [JavaScript Client](https://docs.fal.ai/clients/javascript)
