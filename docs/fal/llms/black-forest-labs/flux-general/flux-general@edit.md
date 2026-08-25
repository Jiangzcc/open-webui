# FLUX.1 [dev] with Controlnets and Loras

> FLUX General Image-to-Image is a versatile endpoint that transforms existing images with support for LoRA, ControlNet, and IP-Adapter extensions, enabling precise control over style transfer, modifications, and artistic variations through multiple guidance methods.


## Overview

- **Endpoint**: `https://fal.run/fal-ai/flux-general/image-to-image`
- **Model ID**: `fal-ai/flux-general/image-to-image`
- **Category**: image-to-image
- **Kind**: inference
**Tags**: lora, controlnet, ip-adapter



## Pricing

- **Price**: $0.075 per megapixels

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

- **`control_loras`** (`list<ControlLoraWeight>`, _optional_):
  The LoRAs to use for the image generation which use a control image. You can use any number of LoRAs
  and they will be merged together to generate the final image.
  - Default: `[]`
  - Array of ControlLoraWeight

- **`controlnets`** (`list<ControlNet>`, _optional_):
  The controlnets to use for the image generation. Only one controlnet is supported at the moment.
  - Default: `[]`
  - Array of ControlNet

- **`controlnet_unions`** (`list<ControlNetUnion>`, _optional_):
  The controlnet unions to use for the image generation. Only one controlnet is supported at the moment.
  - Default: `[]`
  - Array of ControlNetUnion

- **`ip_adapters`** (`list<IPAdapter>`, _optional_):
  IP-Adapter to use for image generation.
  - Default: `[]`
  - Array of IPAdapter

- **`easycontrols`** (`list<EasyControlWeight>`, _optional_):
  EasyControl Inputs to use for image generation.
  - Default: `[]`
  - Array of EasyControlWeight

- **`fill_image`** (`ImageFillInput`, _optional_):
  Use an image input to influence the generation. Can be used to fill images in masked areas.

- **`guidance_scale`** (`float`, _optional_):
  The CFG (Classifier Free Guidance) scale is a measure of how close you want
  the model to stick to your prompt when looking for a related image to show you. Default value: `3.5`
  - Default: `3.5`
  - Range: `0` to `20`

- **`real_cfg_scale`** (`float`, _optional_):
  The CFG (Classifier Free Guidance) scale is a measure of how close you want
  the model to stick to your prompt when looking for a related image to show you. Default value: `3.5`
  - Default: `3.5`
  - Range: `0` to `5`

- **`use_real_cfg`** (`boolean`, _optional_):
  Uses classical CFG as in SD1.5, SDXL, etc. Increases generation times and price when set to be true.
  If using XLabs IP-Adapter v1, this will be turned on!.
  - Default: `false`

- **`use_cfg_zero`** (`boolean`, _optional_):
  Uses CFG-zero init sampling as in https://arxiv.org/abs/2503.18886.
  - Default: `false`

- **`sync_mode`** (`boolean`, _optional_):
  If `True`, the media will be returned as a data URI and the output data won't be available in the request history.
  - Default: `false`

- **`num_images`** (`integer`, _optional_):
  The number of images to generate. This is always set to 1 for streaming output. Default value: `1`
  - Default: `1`
  - Range: `1` to `10`

- **`enable_safety_checker`** (`boolean`, _optional_):
  If set to true, the safety checker will be enabled. Default value: `true`
  - Default: `true`

- **`reference_image_url`** (`string`, _optional_):
  URL of Image for Reference-Only

- **`reference_strength`** (`float`, _optional_):
  Strength of reference_only generation. Only used if a reference image is provided. Default value: `0.65`
  - Default: `0.65`
  - Range: `-3` to `3`

- **`reference_start`** (`float`, _optional_):
  The percentage of the total timesteps when the reference guidance is to bestarted.
  - Default: `0`
  - Range: `0` to `1`

- **`reference_end`** (`float`, _optional_):
  The percentage of the total timesteps when the reference guidance is to be ended. Default value: `1`
  - Default: `1`
  - Range: `0` to `1`

- **`base_shift`** (`float`, _optional_):
  Base shift for the scheduled timesteps Default value: `0.5`
  - Default: `0.5`
  - Range: `0.01` to `5`

- **`max_shift`** (`float`, _optional_):
  Max shift for the scheduled timesteps Default value: `1.15`
  - Default: `1.15`
  - Range: `0.01` to `5`

- **`output_format`** (`OutputFormatEnum`, _optional_):
  The format of the generated image. Default value: `"png"`
  - Default: `"png"`
  - Options: `"jpeg"`, `"png"`

- **`use_beta_schedule`** (`boolean`, _optional_):
  Specifies whether beta sigmas ought to be used.
  - Default: `false`

- **`sigma_schedule`** (`string`, _optional_):
  Sigmas schedule for the denoising process.

- **`scheduler`** (`SchedulerEnum`, _optional_):
  Scheduler for the denoising process. Default value: `"euler"`
  - Default: `"euler"`
  - Options: `"euler"`, `"dpmpp_2m"`

- **`negative_prompt`** (`string`, _optional_):
  Negative prompt to steer the image generation away from unwanted features.
  By default, we will be using NAG for processing the negative prompt. Default value: `""`
  - Default: `""`

- **`nag_scale`** (`float`, _optional_):
  The scale for NAG. Higher values will result in a image that is more distant
  to the negative prompt. Default value: `3`
  - Default: `3`
  - Range: `2` to `10`

- **`nag_tau`** (`float`, _optional_):
  The tau for NAG. Controls the normalization of the hidden state.
  Higher values will result in a less aggressive normalization,
  but may also lead to unexpected changes with respect to the original image.
  Not recommended to change this value. Default value: `2.5`
  - Default: `2.5`

- **`nag_alpha`** (`float`, _optional_):
  The alpha value for NAG. This value is used as a final weighting
  factor for steering the normalized guidance (positive and negative prompts)
  in the direction of the positive prompt. Higher values will result in less
  steering on the normalized guidance where lower values will result in
  considering the positive prompt guidance more. Default value: `0.25`
  - Default: `0.25`

- **`nag_end`** (`float`, _optional_):
  The proportion of steps to apply NAG. After the specified proportion
  of steps has been iterated, the remaining steps will use original
  attention processors in FLUX. Default value: `0.25`
  - Default: `0.25`

- **`image_url`** (`string`, _required_):
  URL of image to use for inpainting. or img2img
  - Examples: "https://raw.githubusercontent.com/CompVis/latent-diffusion/main/data/inpainting_examples/overture-creations-5sI6fQgYIuo.png"

- **`strength`** (`float`, _optional_):
  The strength to use for inpainting/image-to-image. Only used if the image_url is provided. 1.0 is completely remakes the image while 0.0 preserves the original. Default value: `0.85`
  - Default: `0.85`
  - Range: `0.01` to `1`



**Required Parameters Example**:

```json
{
  "prompt": "A photo of a lion sitting on a stone bench",
  "image_url": "https://raw.githubusercontent.com/CompVis/latent-diffusion/main/data/inpainting_examples/overture-creations-5sI6fQgYIuo.png"
}
```

**Full Example**:

```json
{
  "prompt": "A photo of a lion sitting on a stone bench",
  "num_inference_steps": 28,
  "controlnets": [],
  "controlnet_unions": [],
  "ip_adapters": [],
  "easycontrols": [],
  "guidance_scale": 3.5,
  "real_cfg_scale": 3.5,
  "num_images": 1,
  "enable_safety_checker": true,
  "reference_strength": 0.65,
  "reference_end": 1,
  "base_shift": 0.5,
  "max_shift": 1.15,
  "output_format": "png",
  "scheduler": "euler",
  "nag_scale": 3,
  "nag_tau": 2.5,
  "nag_alpha": 0.25,
  "nag_end": 0.25,
  "image_url": "https://raw.githubusercontent.com/CompVis/latent-diffusion/main/data/inpainting_examples/overture-creations-5sI6fQgYIuo.png",
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
  --url https://fal.run/fal-ai/flux-general/image-to-image \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "A photo of a lion sitting on a stone bench",
     "image_url": "https://raw.githubusercontent.com/CompVis/latent-diffusion/main/data/inpainting_examples/overture-creations-5sI6fQgYIuo.png"
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
    "fal-ai/flux-general/image-to-image",
    arguments={
        "prompt": "A photo of a lion sitting on a stone bench",
        "image_url": "https://raw.githubusercontent.com/CompVis/latent-diffusion/main/data/inpainting_examples/overture-creations-5sI6fQgYIuo.png"
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

const result = await fal.subscribe("fal-ai/flux-general/image-to-image", {
  input: {
    prompt: "A photo of a lion sitting on a stone bench",
    image_url: "https://raw.githubusercontent.com/CompVis/latent-diffusion/main/data/inpainting_examples/overture-creations-5sI6fQgYIuo.png"
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

- [Model Playground](https://fal.ai/models/fal-ai/flux-general/image-to-image)
- [API Documentation](https://fal.ai/models/fal-ai/flux-general/image-to-image/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/flux-general/image-to-image)

### fal.ai Platform

- [Platform Documentation](https://docs.fal.ai)
- [Python Client](https://docs.fal.ai/clients/python)
- [JavaScript Client](https://docs.fal.ai/clients/javascript)
