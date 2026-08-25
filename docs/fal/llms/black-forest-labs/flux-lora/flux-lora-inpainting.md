# FLUX.1 [dev] Inpainting with LoRAs

> Super fast endpoint for the FLUX.1 [dev] inpainting model with LoRA support, enabling rapid and high-quality image inpaingting using pre-trained LoRA adaptations for personalization, specific styles, brand identities, and product-specific outputs.


## Overview

- **Endpoint**: `https://fal.run/fal-ai/flux-lora/inpainting`
- **Model ID**: `fal-ai/flux-lora/inpainting`
- **Category**: text-to-image
- **Kind**: inference
**Tags**: lora, personalization



## Pricing

- **Price**: $0.035 per megapixels

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _required_):
  The prompt to generate an image from.
  - Examples: "A photo of a lion sitting on a stone bench"

- **`image_size`** (`ImageSize | Enum`, _optional_):
  The size of the generated image.
  - One of: ImageSize | Enum

- **`num_inference_steps`** (`integer`, _optional_):
  The number of inference steps to perform. Default value: `28`
  - Default: `28`
  - Range: `1` to `50`

- **`seed`** (`integer`, _optional_):
  The same seed and the same prompt given to the same version of the model
  will output the same image every time.

- **`loras`** (`list<LoraWeight>`, _optional_):
  The LoRAs to use for the image generation. You can use any number of LoRAs
  and they will be merged together to generate the final image.
  - Default: `[]`
  - Array of LoraWeight

- **`guidance_scale`** (`float`, _optional_):
  The CFG (Classifier Free Guidance) scale is a measure of how close you want
  the model to stick to your prompt when looking for a related image to show you. Default value: `3.5`
  - Default: `3.5`
  - Range: `0` to `35`

- **`sync_mode`** (`boolean`, _optional_):
  If `True`, the media will be returned as a data URI and the output data won't be available in the request history.
  - Default: `false`

- **`num_images`** (`integer`, _optional_):
  The number of images to generate. This is always set to 1 for streaming output. Default value: `1`
  - Default: `1`
  - Range: `1` to `4`

- **`enable_safety_checker`** (`boolean`, _optional_):
  If set to true, the safety checker will be enabled. Default value: `true`
  - Default: `true`

- **`output_format`** (`OutputFormatEnum`, _optional_):
  The format of the generated image. Default value: `"jpeg"`
  - Default: `"jpeg"`
  - Options: `"jpeg"`, `"png"`

- **`acceleration`** (`AccelerationEnum`, _optional_):
  Acceleration level for image generation. 'regular' balances speed and quality. Default value: `"none"`
  - Default: `"none"`
  - Options: `"none"`, `"regular"`

- **`image_url`** (`string`, _required_):
  URL of image to use for inpainting. or img2img
  - Examples: "https://storage.googleapis.com/falserverless/example_inputs/dog.png"

- **`strength`** (`float`, _optional_):
  The strength to use for inpainting/image-to-image. Only used if the image_url is provided. 1.0 is completely remakes the image while 0.0 preserves the original. Default value: `0.85`
  - Default: `0.85`
  - Range: `0.01` to `1`

- **`mask_url`** (`string`, _required_):
  The mask to area to Inpaint in.
  - Examples: "https://storage.googleapis.com/falserverless/example_inputs/dog_mask.png"



**Required Parameters Example**:

```json
{
  "prompt": "A photo of a lion sitting on a stone bench",
  "image_url": "https://storage.googleapis.com/falserverless/example_inputs/dog.png",
  "mask_url": "https://storage.googleapis.com/falserverless/example_inputs/dog_mask.png"
}
```

**Full Example**:

```json
{
  "prompt": "A photo of a lion sitting on a stone bench",
  "num_inference_steps": 28,
  "guidance_scale": 3.5,
  "num_images": 1,
  "enable_safety_checker": true,
  "output_format": "jpeg",
  "acceleration": "none",
  "image_url": "https://storage.googleapis.com/falserverless/example_inputs/dog.png",
  "strength": 0.85,
  "mask_url": "https://storage.googleapis.com/falserverless/example_inputs/dog_mask.png"
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
  --url https://fal.run/fal-ai/flux-lora/inpainting \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "A photo of a lion sitting on a stone bench",
     "image_url": "https://storage.googleapis.com/falserverless/example_inputs/dog.png",
     "mask_url": "https://storage.googleapis.com/falserverless/example_inputs/dog_mask.png"
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
    "fal-ai/flux-lora/inpainting",
    arguments={
        "prompt": "A photo of a lion sitting on a stone bench",
        "image_url": "https://storage.googleapis.com/falserverless/example_inputs/dog.png",
        "mask_url": "https://storage.googleapis.com/falserverless/example_inputs/dog_mask.png"
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

const result = await fal.subscribe("fal-ai/flux-lora/inpainting", {
  input: {
    prompt: "A photo of a lion sitting on a stone bench",
    image_url: "https://storage.googleapis.com/falserverless/example_inputs/dog.png",
    mask_url: "https://storage.googleapis.com/falserverless/example_inputs/dog_mask.png"
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

- [Model Playground](https://fal.ai/models/fal-ai/flux-lora/inpainting)
- [API Documentation](https://fal.ai/models/fal-ai/flux-lora/inpainting/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/flux-lora/inpainting)

### fal.ai Platform

- [Platform Documentation](https://docs.fal.ai)
- [Python Client](https://docs.fal.ai/clients/python)
- [JavaScript Client](https://docs.fal.ai/clients/javascript)
