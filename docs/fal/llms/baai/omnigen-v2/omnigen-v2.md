# Omnigen V2

> OmniGen is a unified image generation model that can generate a wide range of images from multi-modal prompts. It can be used for various tasks such as Image Editing, Personalized Image Generation, Virtual Try-On, Multi Person Generation and more!


## Overview

- **Endpoint**: `https://fal.run/fal-ai/omnigen-v2`
- **Model ID**: `fal-ai/omnigen-v2`
- **Category**: text-to-image
- **Kind**: inference
**Tags**: multimodal, editing, try-on



## Pricing

- **Price**: $0.15 per megapixels

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _required_):
  The prompt to generate or edit an image. Use specific language like 'Add the bird from image 1 to the desk in image 2' for better results.
  - Examples: "Make the dress blue", "Add a fisherman hat to the woman's head", "Replace the sword with a hammer.", "Change the dress to blue.", "Remove the cat"

- **`input_image_urls`** (`list<string>`, _optional_):
  URLs of input images to use for image editing or multi-image generation. Support up to 3 images.
  - Default: `[]`
  - Array of string
  - Examples: ["https://storage.googleapis.com/falserverless/omnigen/input.png"]

- **`image_size`** (`ImageSize | Enum`, _optional_):
  The size of the generated image. Default value: `square_hd`
  - Default: `"square_hd"`
  - One of: ImageSize | Enum

- **`num_inference_steps`** (`integer`, _optional_):
  The number of inference steps to perform. Default value: `50`
  - Default: `50`
  - Range: `20` to `50`

- **`seed`** (`integer`, _optional_):
  The same seed and the same prompt given to the same version of the model
  will output the same image every time.

- **`text_guidance_scale`** (`float`, _optional_):
  The Text Guidance scale controls how closely the model follows the text prompt.
  Higher values make the model stick more closely to the prompt. Default value: `5`
  - Default: `5`
  - Range: `1` to `8`

- **`image_guidance_scale`** (`float`, _optional_):
  The Image Guidance scale controls how closely the model follows the input images.
  For image editing: 1.3-2.0, for in-context generation: 2.0-3.0 Default value: `2`
  - Default: `2`
  - Range: `1` to `3`

- **`negative_prompt`** (`string`, _optional_):
  Negative prompt to guide what should not be in the image. Default value: `"(((deformed))), blurry, over saturation, bad anatomy, disfigured, poorly drawn face, mutation, mutated, (extra_limb), (ugly), (poorly drawn hands), fused fingers, messy drawing, broken legs censor, censored, censor_bar"`
  - Default: `"(((deformed))), blurry, over saturation, bad anatomy, disfigured, poorly drawn face, mutation, mutated, (extra_limb), (ugly), (poorly drawn hands), fused fingers, messy drawing, broken legs censor, censored, censor_bar"`

- **`cfg_range_start`** (`float`, _optional_):
  CFG range start value.
  - Default: `0`
  - Range: `0` to `1`

- **`cfg_range_end`** (`float`, _optional_):
  CFG range end value. Default value: `1`
  - Default: `1`
  - Range: `0` to `1`

- **`scheduler`** (`SchedulerEnum`, _optional_):
  The scheduler to use for the diffusion process. Default value: `"euler"`
  - Default: `"euler"`
  - Options: `"euler"`, `"dpmsolver"`

- **`sync_mode`** (`boolean`, _optional_):
  If `True`, the media will be returned as a data URI and the output data won't be available in the request history.
  - Default: `false`

- **`num_images`** (`integer`, _optional_):
  The number of images to generate. Default value: `1`
  - Default: `1`
  - Range: `1` to `4`

- **`enable_safety_checker`** (`boolean`, _optional_):
  If set to true, the safety checker will be enabled. Default value: `true`
  - Default: `true`

- **`output_format`** (`OutputFormatEnum`, _optional_):
  The format of the generated image. Default value: `"jpeg"`
  - Default: `"jpeg"`
  - Options: `"jpeg"`, `"png"`



**Required Parameters Example**:

```json
{
  "prompt": "Make the dress blue"
}
```

**Full Example**:

```json
{
  "prompt": "Make the dress blue",
  "input_image_urls": [
    "https://storage.googleapis.com/falserverless/omnigen/input.png"
  ],
  "image_size": "square_hd",
  "num_inference_steps": 50,
  "text_guidance_scale": 5,
  "image_guidance_scale": 2,
  "negative_prompt": "(((deformed))), blurry, over saturation, bad anatomy, disfigured, poorly drawn face, mutation, mutated, (extra_limb), (ugly), (poorly drawn hands), fused fingers, messy drawing, broken legs censor, censored, censor_bar",
  "cfg_range_end": 1,
  "scheduler": "euler",
  "num_images": 1,
  "enable_safety_checker": true,
  "output_format": "jpeg"
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
  --url https://fal.run/fal-ai/omnigen-v2 \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "Make the dress blue"
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
    "fal-ai/omnigen-v2",
    arguments={
        "prompt": "Make the dress blue"
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

const result = await fal.subscribe("fal-ai/omnigen-v2", {
  input: {
    prompt: "Make the dress blue"
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

- [Model Playground](https://fal.ai/models/fal-ai/omnigen-v2)
- [API Documentation](https://fal.ai/models/fal-ai/omnigen-v2/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/omnigen-v2)

### fal.ai Platform

- [Platform Documentation](https://docs.fal.ai)
- [Python Client](https://docs.fal.ai/clients/python)
- [JavaScript Client](https://docs.fal.ai/clients/javascript)
