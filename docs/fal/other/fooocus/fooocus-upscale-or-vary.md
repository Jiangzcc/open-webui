# Fooocus Upscale or Vary

> Default parameters with automated optimizations and quality improvements.


## Overview

- **Endpoint**: `https://fal.run/fal-ai/fooocus/upscale-or-vary`
- **Model ID**: `fal-ai/fooocus/upscale-or-vary`
- **Category**: text-to-image
- **Kind**: inference
**Tags**: upscaling, vary, stylized



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
  - Examples: "a basket of various fruits, bokeh, realistic, masterpiece"

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

- **`uov_image_url`** (`string`, _required_):
  The image to upscale or vary.
  - Examples: "https://storage.googleapis.com/falserverless/model_tests/fooocus/fruit_basket.jpeg"

- **`uov_method`** (`UOVMethodEnum`, _optional_):
  The method to use for upscaling or varying. Default value: `"Vary (Strong)"`
  - Default: `"Vary (Strong)"`
  - Options: `"Disabled"`, `"Vary (Subtle)"`, `"Vary (Strong)"`, `"Upscale (1.5x)"`, `"Upscale (2x)"`, `"Upscale (Fast 2x)"`

- **`image_prompt_1`** (`ImagePrompt`, _optional_)

- **`image_prompt_2`** (`ImagePrompt`, _optional_)

- **`image_prompt_3`** (`ImagePrompt`, _optional_)

- **`image_prompt_4`** (`ImagePrompt`, _optional_)

- **`mixing_image_prompt_and_vary_upscale`** (`boolean`, _optional_):
  Mixing Image Prompt and Vary/Upscale
  - Default: `false`

- **`enable_safety_checker`** (`boolean`, _optional_):
  If set to false, the safety checker will be disabled. Default value: `true`
  - Default: `true`



**Required Parameters Example**:

```json
{
  "uov_image_url": "https://storage.googleapis.com/falserverless/model_tests/fooocus/fruit_basket.jpeg"
}
```

**Full Example**:

```json
{
  "prompt": "a basket of various fruits, bokeh, realistic, masterpiece",
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
  "uov_image_url": "https://storage.googleapis.com/falserverless/model_tests/fooocus/fruit_basket.jpeg",
  "uov_method": "Vary (Strong)",
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
  --url https://fal.run/fal-ai/fooocus/upscale-or-vary \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "uov_image_url": "https://storage.googleapis.com/falserverless/model_tests/fooocus/fruit_basket.jpeg"
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
    "fal-ai/fooocus/upscale-or-vary",
    arguments={
        "uov_image_url": "https://storage.googleapis.com/falserverless/model_tests/fooocus/fruit_basket.jpeg"
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

const result = await fal.subscribe("fal-ai/fooocus/upscale-or-vary", {
  input: {
    uov_image_url: "https://storage.googleapis.com/falserverless/model_tests/fooocus/fruit_basket.jpeg"
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

- [Model Playground](https://fal.ai/models/fal-ai/fooocus/upscale-or-vary)
- [API Documentation](https://fal.ai/models/fal-ai/fooocus/upscale-or-vary/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/fooocus/upscale-or-vary)
- [GitHub Repository](https://github.com/lllyasviel/Fooocus/blob/main/LICENSE)

### fal.ai Platform

- [Platform Documentation](https://docs.fal.ai)
- [Python Client](https://docs.fal.ai/clients/python)
- [JavaScript Client](https://docs.fal.ai/clients/javascript)
