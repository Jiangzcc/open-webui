# Fooocus Inpainting

> Default parameters with automated optimizations and quality improvements.


## Overview

- **Endpoint**: `https://fal.run/fal-ai/fooocus/inpaint`
- **Model ID**: `fal-ai/fooocus/inpaint`
- **Category**: text-to-image
- **Kind**: inference
**Tags**: stylized, editing



## Pricing

- **Price**: $0 per compute seconds

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _optional_):
  The prompt to use for generating the image. Be as descriptive as possible for best results. Default value: `""`
  - Default: `""`
  - Examples: "a cat on a bench, realistic, highly detailed, 8k"

- **`negative_prompt`** (`string`, _optional_):
  The negative prompt to use. Use it to address details that you don't want
  in the image. This could be colors, objects, scenery and even the small details
  (e.g. moustache, blurry, low resolution). Default value: `""`
  - Default: `""`
  - Examples: "(worst quality, low quality, normal quality, lowres, low details, oversaturated, undersaturated, overexposed, underexposed, grayscale, bw, bad photo, bad photography, bad art:1.4), (watermark, signature, text font, username, error, logo, words, letters, digits, autograph, trademark, name:1.2), (blur, blurry, grainy), morbid, ugly, asymmetrical, mutated malformed, mutilated, poorly lit, bad shadow, draft, cropped, out of frame, cut off, censored, jpeg artifacts, out of focus, glitch, duplicate, (airbrushed, cartoon, anime, semi-realistic, cgi, render, blender, digital art, manga, amateur:1.3), (3D ,3D Game, 3D Game Scene, 3D Character:1.1), (bad hands, bad anatomy, bad body, bad face, bad teeth, bad arms, bad legs, deformities:1.3)"

- **`styles`** (`list<Enum>`, _optional_):
  The style to use.
  - Default: `["Fooocus Enhance","Fooocus V2","Fooocus Sharp"]`
  - Array of Enum

- **`performance`** (`PerformanceEnum`, _optional_):
  You can choose Speed or Quality Default value: `"Extreme Speed"`
  - Default: `"Extreme Speed"`
  - Options: `"Speed"`, `"Quality"`, `"Extreme Speed"`, `"Lightning"`

- **`guidance_scale`** (`float`, _optional_):
  The CFG (Classifier Free Guidance) scale is a measure of how close you want
  the model to stick to your prompt when looking for a related image to show you. Default value: `4`
  - Default: `4`
  - Range: `1` to `30`

- **`sharpness`** (`float`, _optional_):
  The sharpness of the generated image. Use it to control how sharp the generated
  image should be. Higher value means image and texture are sharper. Default value: `2`
  - Default: `2`
  - Range: `0` to `30`

- **`aspect_ratio`** (`string`, _optional_):
  The size of the generated image. You can choose between some presets or
  custom height and width that **must be multiples of 8**. Default value: `"1024x1024"`
  - Default: `"1024x1024"`

- **`num_images`** (`integer`, _optional_):
  Number of images to generate in one request Default value: `1`
  - Default: `1`
  - Range: `1` to `4`

- **`loras`** (`list<LoraWeight>`, _optional_):
  The LoRAs to use for the image generation. You can use up to 5 LoRAs
  and they will be merged together to generate the final image.
  - Default: `[{"scale":0.1,"path":"https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/resolve/main/sd_xl_offset_example-lora_1.0.safetensors"}]`
  - Array of LoraWeight

- **`refiner_model`** (`RefinerModelEnum`, _optional_):
  Refiner (SDXL or SD 1.5) Default value: `"None"`
  - Default: `"None"`
  - Options: `"None"`, `"realisticVisionV60B1_v51VAE.safetensors"`

- **`refiner_switch`** (`float`, _optional_):
  Use 0.4 for SD1.5 realistic models; 0.667 for SD1.5 anime models
  0.8 for XL-refiners; or any value for switching two SDXL models. Default value: `0.8`
  - Default: `0.8`
  - Range: `0` to `1`, step: `0.0001`

- **`output_format`** (`OutputFormatEnum`, _optional_):
  The format of the generated image. Default value: `"jpeg"`
  - Default: `"jpeg"`
  - Options: `"png"`, `"jpeg"`, `"webp"`

- **`sync_mode`** (`boolean`, _optional_):
  If `True`, the media will be returned as a data URI and the output data won't be available in the request history.
  - Default: `false`

- **`seed`** (`integer`, _optional_):
  The same seed and the same prompt given to the same version of Stable Diffusion
  will output the same image every time.
  - Examples: 176400

- **`inpaint_image_url`** (`string`, _required_):
  The image to use as a reference for inpainting.
  - Examples: "https://raw.githubusercontent.com/CompVis/latent-diffusion/main/data/inpainting_examples/overture-creations-5sI6fQgYIuo.png"

- **`mask_image_url`** (`string`, _optional_):
  The image to use as a mask for the generated image.
  - Examples: "https://raw.githubusercontent.com/CompVis/latent-diffusion/main/data/inpainting_examples/overture-creations-5sI6fQgYIuo_mask.png"

- **`inpaint_mode`** (`InpaintModeEnum`, _optional_):
  The mode to use for inpainting. Default value: `"Inpaint or Outpaint (default)"`
  - Default: `"Inpaint or Outpaint (default)"`
  - Options: `"Inpaint or Outpaint (default)"`, `"Improve Detail (face, hand, eyes, etc.)"`, `"Modify Content (add objects, change background, etc.)"`

- **`inpaint_additional_prompt`** (`string`, _optional_):
  Describe what you want to inpaint. Default value: `""`
  - Default: `""`

- **`outpaint_selections`** (`list<Enum>`, _optional_):
  The directions to outpaint.
  - Default: `[]`
  - Array of Enum

- **`override_inpaint_options`** (`boolean`, _optional_):
  If set to true, the advanced inpaint options ('inpaint_disable_initial_latent',
  'inpaint_engine', 'inpaint_strength', 'inpaint_respective_field',
  'inpaint_erode_or_dilate') will be overridden.
  Otherwise, the default values will be used.
  - Default: `false`

- **`inpaint_disable_initial_latent`** (`boolean`, _optional_):
  If set to true, the initial preprocessing will be disabled.
  - Default: `false`

- **`inpaint_engine`** (`InpaintEngineEnum`, _optional_):
  Version of Fooocus inpaint model Default value: `"v2.6"`
  - Default: `"v2.6"`
  - Options: `"None"`, `"v1"`, `"v2.5"`, `"v2.6"`

- **`inpaint_strength`** (`float`, _optional_):
  Same as the denoising strength in A1111 inpaint. Only used in inpaint, not
  used in outpaint. (Outpaint always use 1.0) Default value: `1`
  - Default: `1`

- **`inpaint_respective_field`** (`float`, _optional_):
  The area to inpaint. Value 0 is same as "Only Masked" in A1111. Value 1 is
  same as "Whole Image" in A1111. Only used in inpaint, not used in outpaint.
  (Outpaint always use 1.0) Default value: `0.618`
  - Default: `0.618`
  - Range: `0` to `1`, step: `0.001`

- **`inpaint_erode_or_dilate`** (`float`, _optional_):
  Positive value will make white area in the mask larger, negative value will
  make white area smaller. (default is 0, always process before any mask
  invert)
  - Default: `0`
  - Range: `-64` to `64`, step: `1`

- **`invert_mask`** (`boolean`, _optional_):
  If set to true, the mask will be inverted.
  - Default: `false`

- **`image_prompt_1`** (`ImagePrompt`, _optional_)

- **`image_prompt_2`** (`ImagePrompt`, _optional_)

- **`image_prompt_3`** (`ImagePrompt`, _optional_)

- **`image_prompt_4`** (`ImagePrompt`, _optional_)

- **`mixing_image_prompt_and_inpaint`** (`boolean`, _optional_):
  Mixing Image Prompt and Inpaint
  - Default: `false`

- **`enable_safety_checker`** (`boolean`, _optional_):
  If set to false, the safety checker will be disabled. Default value: `true`
  - Default: `true`



**Required Parameters Example**:

```json
{
  "inpaint_image_url": "https://raw.githubusercontent.com/CompVis/latent-diffusion/main/data/inpainting_examples/overture-creations-5sI6fQgYIuo.png"
}
```

**Full Example**:

```json
{
  "prompt": "a cat on a bench, realistic, highly detailed, 8k",
  "negative_prompt": "(worst quality, low quality, normal quality, lowres, low details, oversaturated, undersaturated, overexposed, underexposed, grayscale, bw, bad photo, bad photography, bad art:1.4), (watermark, signature, text font, username, error, logo, words, letters, digits, autograph, trademark, name:1.2), (blur, blurry, grainy), morbid, ugly, asymmetrical, mutated malformed, mutilated, poorly lit, bad shadow, draft, cropped, out of frame, cut off, censored, jpeg artifacts, out of focus, glitch, duplicate, (airbrushed, cartoon, anime, semi-realistic, cgi, render, blender, digital art, manga, amateur:1.3), (3D ,3D Game, 3D Game Scene, 3D Character:1.1), (bad hands, bad anatomy, bad body, bad face, bad teeth, bad arms, bad legs, deformities:1.3)",
  "styles": [
    "Fooocus Enhance",
    "Fooocus V2",
    "Fooocus Sharp"
  ],
  "performance": "Extreme Speed",
  "guidance_scale": 4,
  "sharpness": 2,
  "aspect_ratio": "1024x1024",
  "num_images": 1,
  "loras": [
    {
      "scale": 0.1,
      "path": "https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/resolve/main/sd_xl_offset_example-lora_1.0.safetensors"
    }
  ],
  "refiner_model": "None",
  "refiner_switch": 0.8,
  "output_format": "jpeg",
  "seed": 176400,
  "inpaint_image_url": "https://raw.githubusercontent.com/CompVis/latent-diffusion/main/data/inpainting_examples/overture-creations-5sI6fQgYIuo.png",
  "mask_image_url": "https://raw.githubusercontent.com/CompVis/latent-diffusion/main/data/inpainting_examples/overture-creations-5sI6fQgYIuo_mask.png",
  "inpaint_mode": "Inpaint or Outpaint (default)",
  "outpaint_selections": [],
  "inpaint_engine": "v2.6",
  "inpaint_strength": 1,
  "inpaint_respective_field": 0.618,
  "enable_safety_checker": true
}
```


### Output Schema

The API returns the following output format:

- **`images`** (`list<Image>`, _required_):
  The generated image file info.
  - Array of Image

- **`timings`** (`Timings`, _required_):
  The time taken for the generation process.

- **`has_nsfw_concepts`** (`list<boolean>`, _required_):
  Whether the generated images contain NSFW concepts.
  - Array of boolean



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
  ]
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/fooocus/inpaint \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "inpaint_image_url": "https://raw.githubusercontent.com/CompVis/latent-diffusion/main/data/inpainting_examples/overture-creations-5sI6fQgYIuo.png"
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
    "fal-ai/fooocus/inpaint",
    arguments={
        "inpaint_image_url": "https://raw.githubusercontent.com/CompVis/latent-diffusion/main/data/inpainting_examples/overture-creations-5sI6fQgYIuo.png"
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

const result = await fal.subscribe("fal-ai/fooocus/inpaint", {
  input: {
    inpaint_image_url: "https://raw.githubusercontent.com/CompVis/latent-diffusion/main/data/inpainting_examples/overture-creations-5sI6fQgYIuo.png"
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

- [Model Playground](https://fal.ai/models/fal-ai/fooocus/inpaint)
- [API Documentation](https://fal.ai/models/fal-ai/fooocus/inpaint/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/fooocus/inpaint)
- [GitHub Repository](https://github.com/lllyasviel/Fooocus/blob/main/LICENSE)

### fal.ai Platform

- [Platform Documentation](https://docs.fal.ai)
- [Python Client](https://docs.fal.ai/clients/python)
- [JavaScript Client](https://docs.fal.ai/clients/javascript)
