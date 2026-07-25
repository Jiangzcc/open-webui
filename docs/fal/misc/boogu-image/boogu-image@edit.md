# Boogu Image

> Image To Image Model using Boogu-Image


## Overview

- **Endpoint**: `https://fal.run/fal-ai/boogu-image/edit`
- **Model ID**: `fal-ai/boogu-image/edit`
- **Category**: image-to-image
- **Kind**: inference


## Pricing

Your request will cost **$0.04** per megapixel of each generated image (a 1024×1024 image is 1 megapixel). For example, a 1MP image costs **$0.04** and a 2048×2048 (4MP) image costs **$0.16**. Generating multiple images multiplies the cost by the number of images.

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _required_):
  The edit instruction describing how to transform the input image. Boogu-Image supports English and Chinese instructions.
  - Examples: "Change the background to a sunny garden while preserving the person.", "帮我在这幅画右下角加上三个带叶子的柿子。"

- **`image_url`** (`string`, _required_):
  URL of the input image to edit.
  - Examples: "https://storage.googleapis.com/falserverless/example_inputs/flux2_dev_edit_input.png"

- **`negative_prompt`** (`string`, _optional_):
  Describes what should NOT appear in the edited image. Used for classifier-free guidance; leave empty to disable text negative guidance. Default value: `""`
  - Default: `""`

- **`image_size`** (`ImageSize | Enum`, _optional_):
  The output size. If omitted, the edited image follows the input image aspect ratio while respecting the model's 2K native limit.
  - One of: ImageSize | Enum

- **`num_inference_steps`** (`integer`, _optional_):
  The number of denoising steps to perform. Default value: `30`
  - Default: `30`
  - Range: `20` to `50`

- **`guidance_scale`** (`float`, _optional_):
  Controls how closely the edit follows the text instruction. Higher values stick more closely to the prompt. Default value: `4`
  - Default: `4`
  - Range: `1` to `8`

- **`image_guidance_scale`** (`float`, _optional_):
  Reference-image guidance strength. A value of 1.0 disables image CFG; higher values preserve the input image more strongly. Default value: `1`
  - Default: `1`
  - Range: `1` to `8`

- **`cfg_range_start`** (`float`, _optional_):
  Start of the timestep fraction over which CFG is applied.
  - Default: `0`
  - Range: `0` to `1`

- **`cfg_range_end`** (`float`, _optional_):
  End of the timestep fraction over which CFG is applied. Default value: `1`
  - Default: `1`
  - Range: `0` to `1`

- **`num_images`** (`integer`, _optional_):
  The number of edited images to generate. Default value: `1`
  - Default: `1`
  - Range: `1` to `4`

- **`seed`** (`integer`, _optional_):
  The same seed, prompt, and input image given to the same version of the model will output the same image every time.

- **`enable_safety_checker`** (`boolean`, _optional_):
  If true, the safety checker is run on the input and output images. Default value: `true`
  - Default: `true`

- **`output_format`** (`OutputFormatEnum`, _optional_):
  The format of the generated image. Default value: `"jpeg"`
  - Default: `"jpeg"`
  - Options: `"jpeg"`, `"png"`

- **`sync_mode`** (`boolean`, _optional_):
  If true, the media is returned as a data URI and the output is not available in the request history.
  - Default: `false`



**Required Parameters Example**:

```json
{
  "prompt": "Change the background to a sunny garden while preserving the person.",
  "image_url": "https://storage.googleapis.com/falserverless/example_inputs/flux2_dev_edit_input.png"
}
```

**Full Example**:

```json
{
  "prompt": "Change the background to a sunny garden while preserving the person.",
  "image_url": "https://storage.googleapis.com/falserverless/example_inputs/flux2_dev_edit_input.png",
  "num_inference_steps": 30,
  "guidance_scale": 4,
  "image_guidance_scale": 1,
  "cfg_range_end": 1,
  "num_images": 1,
  "enable_safety_checker": true,
  "output_format": "jpeg"
}
```


### Output Schema

The API returns the following output format:

- **`images`** (`list<Image>`, _required_):
  The generated images.
  - Array of Image
  - Examples: {"url":"https://storage.googleapis.com/falserverless/example_outputs/boogu_image_t2i.jpeg","height":1024,"content_type":"image/jpeg","width":1024}

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
  "images": {
    "url": "https://storage.googleapis.com/falserverless/example_outputs/boogu_image_t2i.jpeg",
    "height": 1024,
    "content_type": "image/jpeg",
    "width": 1024
  },
  "prompt": ""
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/boogu-image/edit \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "Change the background to a sunny garden while preserving the person.",
     "image_url": "https://storage.googleapis.com/falserverless/example_inputs/flux2_dev_edit_input.png"
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
    "fal-ai/boogu-image/edit",
    arguments={
        "prompt": "Change the background to a sunny garden while preserving the person.",
        "image_url": "https://storage.googleapis.com/falserverless/example_inputs/flux2_dev_edit_input.png"
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

const result = await fal.subscribe("fal-ai/boogu-image/edit", {
  input: {
    prompt: "Change the background to a sunny garden while preserving the person.",
    image_url: "https://storage.googleapis.com/falserverless/example_inputs/flux2_dev_edit_input.png"
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

- [Model Playground](https://fal.ai/models/fal-ai/boogu-image/edit)
- [API Documentation](https://fal.ai/models/fal-ai/boogu-image/edit/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/boogu-image/edit)

### fal.ai Platform

- [Platform Documentation](https://docs.fal.ai)
- [Python Client](https://docs.fal.ai/clients/python)
- [JavaScript Client](https://docs.fal.ai/clients/javascript)
