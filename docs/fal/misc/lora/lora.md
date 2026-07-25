# Stable Diffusion with LoRAs

> Run Any Stable Diffusion model with customizable LoRA weights.


## Overview

- **Endpoint**: `https://fal.run/fal-ai/lora`
- **Model ID**: `fal-ai/lora`
- **Category**: text-to-image
- **Kind**: inference
**Tags**: diffusion, lora, customization



## Pricing

- **Price**: $0 per compute seconds

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`model_name`** (`string`, _required_):
  URL or HuggingFace ID of the base model to generate the image.
  - Examples: "stabilityai/stable-diffusion-xl-base-1.0", "runwayml/stable-diffusion-v1-5", "SG161222/Realistic_Vision_V2.0"

- **`unet_name`** (`string`, _optional_):
  URL or HuggingFace ID of the custom U-Net model to use for the image generation.

- **`variant`** (`string`, _optional_):
  The variant of the model to use for huggingface models, e.g. 'fp16'.

- **`prompt`** (`string`, _required_):
  The prompt to use for generating the image. Be as descriptive as possible for best results.
  - Examples: "Photo of a european medieval 40 year old queen, silver hair, highly detailed face, detailed eyes, head shot, intricate crown, age spots, wrinkles", "Photo of a classic red mustang car parked in las vegas strip at night"

- **`negative_prompt`** (`string`, _optional_):
  The negative prompt to use.Use it to address details that you don't want
  in the image. This could be colors, objects, scenery and even the small details
  (e.g. moustache, blurry, low resolution). Default value: `""`
  - Default: `""`
  - Examples: "cartoon, painting, illustration, worst quality, low quality, normal quality"

- **`prompt_weighting`** (`boolean`, _optional_):
  If set to true, the prompt weighting syntax will be used.
  Additionally, this will lift the 77 token limit by averaging embeddings.
  - Default: `false`
  - Examples: true

- **`loras`** (`list<LoraWeight>`, _optional_):
  The LoRAs to use for the image generation. You can use any number of LoRAs
  and they will be merged together to generate the final image.
  - Default: `[]`
  - Array of LoraWeight

- **`embeddings`** (`list<Embedding>`, _optional_):
  The embeddings to use for the image generation. Only a single embedding is supported at the moment.
  The embeddings will be used to map the tokens in the prompt to the embedding weights.
  - Default: `[]`
  - Array of Embedding

- **`controlnets`** (`list<ControlNet>`, _optional_):
  The control nets to use for the image generation. You can use any number of control nets
  and they will be applied to the image at the specified timesteps.
  - Default: `[]`
  - Array of ControlNet

- **`controlnet_guess_mode`** (`boolean`, _optional_):
  If set to true, the controlnet will be applied to only the conditional predictions.
  - Default: `false`

- **`ip_adapter`** (`list<IPAdapter>`, _optional_):
  The IP adapter to use for the image generation.
  - Default: `[]`
  - Array of IPAdapter

- **`image_encoder_path`** (`string`, _optional_):
  The path to the image encoder model to use for the image generation.

- **`image_encoder_subfolder`** (`string`, _optional_):
  The subfolder of the image encoder model to use for the image generation.

- **`image_encoder_weight_name`** (`string`, _optional_):
  The weight name of the image encoder model to use for the image generation. Default value: `"pytorch_model.bin"`
  - Default: `"pytorch_model.bin"`
  - Examples: "pytorch_model.bin"

- **`ic_light_model_url`** (`string`, _optional_):
  The URL of the IC Light model to use for the image generation.

- **`ic_light_model_background_image_url`** (`string`, _optional_):
  The URL of the IC Light model background image to use for the image generation.
  Make sure to use a background compatible with the model.

- **`ic_light_image_url`** (`string`, _optional_):
  The URL of the IC Light model image to use for the image generation.

- **`seed`** (`integer`, _optional_):
  The same seed and the same prompt given to the same version of Stable Diffusion
  will output the same image every time.

- **`image_size`** (`ImageSize | Enum`, _optional_):
  The size of the generated image. You can choose between some presets or custom height and width
  that **must be multiples of 8**. Default value: `square_hd`
  - Default: `"square_hd"`
  - One of: ImageSize | Enum

- **`num_inference_steps`** (`integer`, _optional_):
  Increasing the amount of steps tells Stable Diffusion that it should take more steps
  to generate your final result which can increase the amount of detail in your image. Default value: `30`
  - Default: `30`
  - Range: `1` to `150`

- **`guidance_scale`** (`float`, _optional_):
  The CFG (Classifier Free Guidance) scale is a measure of how close you want
  the model to stick to your prompt when looking for a related image to show you. Default value: `7.5`
  - Default: `7.5`
  - Range: `0` to `20`

- **`clip_skip`** (`integer`, _optional_):
  Skips part of the image generation process, leading to slightly different results.
  This means the image renders faster, too.
  - Default: `0`
  - Range: `0` to `2`

- **`scheduler`** (`Enum`, _optional_):
  Scheduler / sampler to use for the image denoising process.
  - Options: `"DPM++ 2M"`, `"DPM++ 2M Karras"`, `"DPM++ 2M SDE"`, `"DPM++ 2M SDE Karras"`, `"Euler"`, `"Euler A"`, `"Euler (trailing timesteps)"`, `"LCM"`, `"LCM (trailing timesteps)"`, `"DDIM"`, `"TCD"`

- **`timesteps`** (`TimestepsInput`, _optional_):
  Optionally override the timesteps to use for the denoising process. Only works with schedulers which support the `timesteps` argument in their `set_timesteps` method.
  Defaults to not overriding, in which case the scheduler automatically sets the timesteps based on the `num_inference_steps` parameter.
  If set to a custom timestep schedule, the `num_inference_steps` parameter will be ignored. Cannot be set if `sigmas` is set.

- **`sigmas`** (`SigmasInput`, _optional_):
  Optionally override the sigmas to use for the denoising process. Only works with schedulers which support the `sigmas` argument in their `set_sigmas` method.
  Defaults to not overriding, in which case the scheduler automatically sets the sigmas based on the `num_inference_steps` parameter.
  If set to a custom sigma schedule, the `num_inference_steps` parameter will be ignored. Cannot be set if `timesteps` is set.

- **`prediction_type`** (`PredictionTypeEnum`, _optional_):
  The type of prediction to use for the image generation.
  The `epsilon` is the default. Default value: `"epsilon"`
  - Default: `"epsilon"`
  - Options: `"v_prediction"`, `"epsilon"`

- **`rescale_betas_snr_zero`** (`boolean`, _optional_):
  Whether to set the rescale_betas_snr_zero option or not for the sampler
  - Default: `false`

- **`image_format`** (`ImageFormatEnum`, _optional_):
  The format of the generated image. Default value: `"png"`
  - Default: `"png"`
  - Options: `"jpeg"`, `"png"`
  - Examples: "jpeg"

- **`num_images`** (`integer`, _optional_):
  Number of images to generate in one request. Note that the higher the batch size,
  the longer it will take to generate the images. Default value: `1`
  - Default: `1`
  - Range: `1` to `8`

- **`enable_safety_checker`** (`boolean`, _optional_):
  If set to true, the safety checker will be enabled.
  - Default: `false`

- **`tile_width`** (`integer`, _optional_):
  The size of the tiles to be used for the image generation. Default value: `4096`
  - Default: `4096`
  - Range: `128` to `4096`

- **`tile_height`** (`integer`, _optional_):
  The size of the tiles to be used for the image generation. Default value: `4096`
  - Default: `4096`
  - Range: `128` to `4096`

- **`tile_stride_width`** (`integer`, _optional_):
  The stride of the tiles to be used for the image generation. Default value: `2048`
  - Default: `2048`
  - Range: `64` to `2048`

- **`tile_stride_height`** (`integer`, _optional_):
  The stride of the tiles to be used for the image generation. Default value: `2048`
  - Default: `2048`
  - Range: `64` to `2048`

- **`eta`** (`float`, _optional_):
  The eta value to be used for the image generation.
  - Default: `0`
  - Range: `0` to `1`

- **`debug_latents`** (`boolean`, _optional_):
  If set to true, the latents will be saved for debugging.
  - Default: `false`

- **`debug_per_pass_latents`** (`boolean`, _optional_):
  If set to true, the latents will be saved for debugging per pass.
  - Default: `false`



**Required Parameters Example**:

```json
{
  "model_name": "stabilityai/stable-diffusion-xl-base-1.0",
  "prompt": "Photo of a european medieval 40 year old queen, silver hair, highly detailed face, detailed eyes, head shot, intricate crown, age spots, wrinkles"
}
```

**Full Example**:

```json
{
  "model_name": "stabilityai/stable-diffusion-xl-base-1.0",
  "prompt": "Photo of a european medieval 40 year old queen, silver hair, highly detailed face, detailed eyes, head shot, intricate crown, age spots, wrinkles",
  "negative_prompt": "cartoon, painting, illustration, worst quality, low quality, normal quality",
  "prompt_weighting": true,
  "loras": [],
  "embeddings": [],
  "controlnets": [],
  "ip_adapter": [],
  "image_encoder_weight_name": "pytorch_model.bin",
  "image_size": "square_hd",
  "num_inference_steps": 30,
  "guidance_scale": 7.5,
  "prediction_type": "epsilon",
  "image_format": "jpeg",
  "num_images": 1,
  "tile_width": 4096,
  "tile_height": 4096,
  "tile_stride_width": 2048,
  "tile_stride_height": 2048
}
```


### Output Schema

The API returns the following output format:

- **`images`** (`list<Image>`, _required_):
  The generated image files info.
  - Array of Image

- **`seed`** (`integer`, _required_):
  Seed of the generated Image. It will be the same value of the one passed in the
  input or the randomly generated that was used in case none was passed.

- **`has_nsfw_concepts`** (`list<boolean>`, _required_):
  Whether the generated images contain NSFW concepts.
  - Array of boolean

- **`debug_latents`** (`File`, _required_):
  The latents saved for debugging.

- **`debug_per_pass_latents`** (`File`, _required_):
  The latents saved for debugging per pass.



**Example Response**:

```json
{
  "images": [
    {
      "url": "",
      "content_type": "image/png",
      "file_name": "z9RV14K95DvU.png",
      "file_size": 4404019,
      "width": 1024,
      "height": 1024
    }
  ],
  "debug_latents": {
    "url": "",
    "content_type": "image/png",
    "file_name": "z9RV14K95DvU.png",
    "file_size": 4404019
  },
  "debug_per_pass_latents": {
    "url": "",
    "content_type": "image/png",
    "file_name": "z9RV14K95DvU.png",
    "file_size": 4404019
  }
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/lora \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "model_name": "stabilityai/stable-diffusion-xl-base-1.0",
     "prompt": "Photo of a european medieval 40 year old queen, silver hair, highly detailed face, detailed eyes, head shot, intricate crown, age spots, wrinkles"
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
    "fal-ai/lora",
    arguments={
        "model_name": "stabilityai/stable-diffusion-xl-base-1.0",
        "prompt": "Photo of a european medieval 40 year old queen, silver hair, highly detailed face, detailed eyes, head shot, intricate crown, age spots, wrinkles"
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

const result = await fal.subscribe("fal-ai/lora", {
  input: {
    model_name: "stabilityai/stable-diffusion-xl-base-1.0",
    prompt: "Photo of a european medieval 40 year old queen, silver hair, highly detailed face, detailed eyes, head shot, intricate crown, age spots, wrinkles"
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

- [Model Playground](https://fal.ai/models/fal-ai/lora)
- [API Documentation](https://fal.ai/models/fal-ai/lora/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/lora)
- [GitHub Repository](https://huggingface.co/spaces/CompVis/stable-diffusion-license)

### fal.ai Platform

- [Platform Documentation](https://docs.fal.ai)
- [Python Client](https://docs.fal.ai/clients/python)
- [JavaScript Client](https://docs.fal.ai/clients/javascript)
