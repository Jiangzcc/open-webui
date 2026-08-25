# FLUX 2 Turbo Edit

> Image-to-image editing with FLUX.2 [dev] from Black Forest Labs. Precise modifications using natural language descriptions and hex color control—all at turbo speed.


## Overview

- **Endpoint**: `https://fal.run/fal-ai/flux-2/turbo/edit`
- **Model ID**: `fal-ai/flux-2/turbo/edit`
- **Category**: image-to-image
- **Kind**: inference


## Pricing

Requests cost **$0.008** per megapixel of input and output. Input images will be resized to 1MP. For example, a 1024x1024 generation with 512*512 size image input will cost **0.016** (1 MP input + 1 MP output, each costing **0.008**).

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _required_):
  The prompt to edit the image.
  - Examples: "Change the weather to winter"

- **`guidance_scale`** (`float`, _optional_):
  Guidance Scale is a measure of how close you want the model to stick to your prompt when looking for a related image to show you. Default value: `2.5`
  - Default: `2.5`
  - Range: `0` to `20`

- **`seed`** (`integer`, _optional_):
  The seed to use for the generation. If not provided, a random seed will be used.

- **`image_size`** (`ImageSize | Enum`, _optional_):
  The size of the image to generate. The width and height must be between 512 and 2048 pixels. Default value: `square_hd`
  - Default: `"square_hd"`
  - One of: ImageSize | Enum

- **`num_images`** (`integer`, _optional_):
  The number of images to generate. Default value: `1`
  - Default: `1`
  - Range: `1` to `4`

- **`enable_prompt_expansion`** (`boolean`, _optional_):
  If set to true, the prompt will be expanded for better results.
  - Default: `false`

- **`sync_mode`** (`boolean`, _optional_):
  If `True`, the media will be returned as a data URI and the output data won't be available in the request history.
  - Default: `false`

- **`enable_safety_checker`** (`boolean`, _optional_):
  If set to true, the safety checker will be enabled. Default value: `true`
  - Default: `true`

- **`output_format`** (`OutputFormatEnum`, _optional_):
  The format of the generated image. Default value: `"png"`
  - Default: `"png"`
  - Options: `"jpeg"`, `"png"`, `"webp"`

- **`image_urls`** (`list<string>`, _required_):
  The URLs of the images for editing. A maximum of 4 images are allowed, if more are provided, only the first 4 will be used.
  - Array of string
  - Examples: ["https://storage.googleapis.com/falserverless/example_outputs/flux-2-turbo.png"]



**Required Parameters Example**:

```json
{
  "prompt": "Change the weather to winter",
  "image_urls": [
    "https://storage.googleapis.com/falserverless/example_outputs/flux-2-turbo.png"
  ]
}
```

**Full Example**:

```json
{
  "prompt": "Change the weather to winter",
  "guidance_scale": 2.5,
  "image_size": "square_hd",
  "num_images": 1,
  "enable_safety_checker": true,
  "output_format": "png",
  "image_urls": [
    "https://storage.googleapis.com/falserverless/example_outputs/flux-2-turbo.png"
  ]
}
```


### Output Schema

The API returns the following output format:

- **`images`** (`list<ImageFile>`, _required_):
  The edited images
  - Array of ImageFile
  - Examples: [{"url":"https://storage.googleapis.com/falserverless/example_outputs/flux-2-turbo-edit.png"}]

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
      "url": "https://storage.googleapis.com/falserverless/example_outputs/flux-2-turbo-edit.png"
    }
  ],
  "prompt": ""
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/flux-2/turbo/edit \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "Change the weather to winter",
     "image_urls": [
       "https://storage.googleapis.com/falserverless/example_outputs/flux-2-turbo.png"
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
    "fal-ai/flux-2/turbo/edit",
    arguments={
        "prompt": "Change the weather to winter",
        "image_urls": ["https://storage.googleapis.com/falserverless/example_outputs/flux-2-turbo.png"]
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

const result = await fal.subscribe("fal-ai/flux-2/turbo/edit", {
  input: {
    prompt: "Change the weather to winter",
    image_urls: ["https://storage.googleapis.com/falserverless/example_outputs/flux-2-turbo.png"]
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

- [Model Playground](https://fal.ai/models/fal-ai/flux-2/turbo/edit)
- [API Documentation](https://fal.ai/models/fal-ai/flux-2/turbo/edit/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/flux-2/turbo/edit)

### fal.ai Platform

- [Platform Documentation](https://docs.fal.ai)
- [Python Client](https://docs.fal.ai/clients/python)
- [JavaScript Client](https://docs.fal.ai/clients/javascript)
