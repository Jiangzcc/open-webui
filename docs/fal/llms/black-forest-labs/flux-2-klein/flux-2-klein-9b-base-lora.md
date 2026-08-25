# FLUX.2 [klein] 9B Base LoRA

> Text-to-image generation with LoRA support for FLUX.2 [klein] 9B Base from Black Forest Labs. Custom style adaptation and fine-tuned model variations.


## Overview

- **Endpoint**: `https://fal.run/fal-ai/flux-2/klein/9b/base/lora`
- **Model ID**: `fal-ai/flux-2/klein/9b/base/lora`
- **Category**: text-to-image
- **Kind**: inference


## Pricing

- **Price**: $0.02 per megapixels

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _required_):
  The prompt to generate an image from.
  - Examples: "A serene Japanese garden with cherry blossoms, koi pond, and traditional wooden bridge at golden hour"

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
  The size of the image to generate. Default value: `landscape_4_3`
  - Default: `"landscape_4_3"`
  - One of: ImageSize | Enum

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

- **`loras`** (`list<fal-ai_flux-2-klein_LoRAInput>`, _optional_):
  List of LoRA weights to apply (maximum 3).
  - Default: `[]`
  - Array of fal-ai_flux-2-klein_LoRAInput



**Required Parameters Example**:

```json
{
  "prompt": "A serene Japanese garden with cherry blossoms, koi pond, and traditional wooden bridge at golden hour"
}
```

**Full Example**:

```json
{
  "prompt": "A serene Japanese garden with cherry blossoms, koi pond, and traditional wooden bridge at golden hour",
  "guidance_scale": 5,
  "num_inference_steps": 28,
  "image_size": "landscape_4_3",
  "num_images": 1,
  "acceleration": "regular",
  "enable_safety_checker": true,
  "output_format": "png",
  "loras": []
}
```


### Output Schema

The API returns the following output format:

- **`images`** (`list<ImageFile>`, _required_):
  The generated images
  - Array of ImageFile

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
      "content_type": "image/png",
      "file_name": "z9RV14K95DvU.png",
      "file_size": 4404019
    }
  ],
  "prompt": ""
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/flux-2/klein/9b/base/lora \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "A serene Japanese garden with cherry blossoms, koi pond, and traditional wooden bridge at golden hour"
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
    "fal-ai/flux-2/klein/9b/base/lora",
    arguments={
        "prompt": "A serene Japanese garden with cherry blossoms, koi pond, and traditional wooden bridge at golden hour"
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

const result = await fal.subscribe("fal-ai/flux-2/klein/9b/base/lora", {
  input: {
    prompt: "A serene Japanese garden with cherry blossoms, koi pond, and traditional wooden bridge at golden hour"
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

- [Model Playground](https://fal.ai/models/fal-ai/flux-2/klein/9b/base/lora)
- [API Documentation](https://fal.ai/models/fal-ai/flux-2/klein/9b/base/lora/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/flux-2/klein/9b/base/lora)

### fal.ai Platform

- [Platform Documentation](https://docs.fal.ai)
- [Python Client](https://docs.fal.ai/clients/python)
- [JavaScript Client](https://docs.fal.ai/clients/javascript)
