# FLUX.1 [dev] Control LoRA Depth

> FLUX Control LoRA Depth is a high-performance endpoint that uses a control image using a depth map to transfer structure to the generated image and another initial image to guide color.


## Overview

- **Endpoint**: `https://fal.run/fal-ai/flux-control-lora-depth/image-to-image`
- **Model ID**: `fal-ai/flux-control-lora-depth/image-to-image`
- **Category**: image-to-image
- **Kind**: inference
**Tags**: lora, style transfer



## Pricing

- **Price**: $0.04 per megapixels

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _required_):
  The prompt to generate an image from.
  - Examples: "A photo of a lion sitting on a stone bench"

- **`image_url`** (`string`, _required_):
  URL of image to use for inpainting. or img2img
  - Examples: "https://raw.githubusercontent.com/CompVis/latent-diffusion/main/data/inpainting_examples/overture-creations-5sI6fQgYIuo.png"

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

- **`control_lora_image_url`** (`string`, _required_):
  The image to use for control lora. This is used to control the style of the generated image.
  - Examples: "https://v3.fal.media/files/kangaroo/Cb7BeM7G4DauK_lWjzY3N_Celeb6.jpg"

- **`control_lora_strength`** (`float`, _optional_):
  The strength of the control lora. Default value: `1`
  - Default: `1`
  - Range: `0` to `2`

- **`strength`** (`float`, _optional_):
  The strength to use for inpainting/image-to-image. Only used if the image_url is provided. 1.0 is completely remakes the image while 0.0 preserves the original. Default value: `0.85`
  - Default: `0.85`
  - Range: `0.01` to `1`



**Required Parameters Example**:

```json
{
  "prompt": "A photo of a lion sitting on a stone bench",
  "image_url": "https://raw.githubusercontent.com/CompVis/latent-diffusion/main/data/inpainting_examples/overture-creations-5sI6fQgYIuo.png",
  "control_lora_image_url": "https://v3.fal.media/files/kangaroo/Cb7BeM7G4DauK_lWjzY3N_Celeb6.jpg"
}
```

**Full Example**:

```json
{
  "prompt": "A photo of a lion sitting on a stone bench",
  "image_url": "https://raw.githubusercontent.com/CompVis/latent-diffusion/main/data/inpainting_examples/overture-creations-5sI6fQgYIuo.png",
  "num_inference_steps": 28,
  "guidance_scale": 3.5,
  "num_images": 1,
  "enable_safety_checker": true,
  "output_format": "jpeg",
  "control_lora_image_url": "https://v3.fal.media/files/kangaroo/Cb7BeM7G4DauK_lWjzY3N_Celeb6.jpg",
  "control_lora_strength": 1,
  "strength": 0.85
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
  --url https://fal.run/fal-ai/flux-control-lora-depth/image-to-image \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "A photo of a lion sitting on a stone bench",
     "image_url": "https://raw.githubusercontent.com/CompVis/latent-diffusion/main/data/inpainting_examples/overture-creations-5sI6fQgYIuo.png",
     "control_lora_image_url": "https://v3.fal.media/files/kangaroo/Cb7BeM7G4DauK_lWjzY3N_Celeb6.jpg"
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
    "fal-ai/flux-control-lora-depth/image-to-image",
    arguments={
        "prompt": "A photo of a lion sitting on a stone bench",
        "image_url": "https://raw.githubusercontent.com/CompVis/latent-diffusion/main/data/inpainting_examples/overture-creations-5sI6fQgYIuo.png",
        "control_lora_image_url": "https://v3.fal.media/files/kangaroo/Cb7BeM7G4DauK_lWjzY3N_Celeb6.jpg"
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

const result = await fal.subscribe("fal-ai/flux-control-lora-depth/image-to-image", {
  input: {
    prompt: "A photo of a lion sitting on a stone bench",
    image_url: "https://raw.githubusercontent.com/CompVis/latent-diffusion/main/data/inpainting_examples/overture-creations-5sI6fQgYIuo.png",
    control_lora_image_url: "https://v3.fal.media/files/kangaroo/Cb7BeM7G4DauK_lWjzY3N_Celeb6.jpg"
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

- [Model Playground](https://fal.ai/models/fal-ai/flux-control-lora-depth/image-to-image)
- [API Documentation](https://fal.ai/models/fal-ai/flux-control-lora-depth/image-to-image/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/flux-control-lora-depth/image-to-image)

### fal.ai Platform

- [Platform Documentation](https://docs.fal.ai)
- [Python Client](https://docs.fal.ai/clients/python)
- [JavaScript Client](https://docs.fal.ai/clients/javascript)
