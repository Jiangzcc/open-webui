# Illusion Diffusion

> Create illusions conditioned on image.


## Overview

- **Endpoint**: `https://fal.run/fal-ai/illusion-diffusion`
- **Model ID**: `fal-ai/illusion-diffusion`
- **Category**: text-to-image
- **Kind**: inference
**Tags**: composition, stylized



## Pricing

- **Price**: $0 per compute seconds

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`image_url`** (`string`, _required_):
  Input image url.
  - Examples: "https://storage.googleapis.com/falserverless/illusion-examples/pattern.png", "https://storage.googleapis.com/falserverless/illusion-examples/checkers.png", "https://storage.googleapis.com/falserverless/illusion-examples/checkers_mid.jpg", "https://storage.googleapis.com/falserverless/illusion-examples/ultra_checkers.png", "https://storage.googleapis.com/falserverless/illusion-examples/funky.jpeg", "https://storage.googleapis.com/falserverless/illusion-examples/cubes.jpeg", "https://storage.googleapis.com/falserverless/illusion-examples/turkey-flag.png", "https://storage.googleapis.com/falserverless/illusion-examples/india-flag.png", "https://storage.googleapis.com/falserverless/illusion-examples/usa-flag.png"

- **`prompt`** (`string`, _required_):
  The prompt to use for generating the image. Be as descriptive as possible for best results.
  - Examples: "(masterpiece:1.4), (best quality), (detailed), Medieval village scene with busy streets and castle in the distance"

- **`negative_prompt`** (`string`, _optional_):
  The negative prompt to use. Use it to address details that you don't want
  in the image. This could be colors, objects, scenery and even the small details
  (e.g. moustache, blurry, low resolution). Default value: `""`
  - Default: `""`
  - Examples: "(worst quality, poor details:1.4), lowres, (artist name, signature, watermark:1.4), bad-artist-anime, bad_prompt_version2, bad-hands-5, ng_deepnegative_v1_75t"

- **`guidance_scale`** (`float`, _optional_):
  The CFG (Classifier Free Guidance) scale is a measure of how close you want
  the model to stick to your prompt when looking for a related image to show you. Default value: `7.5`
  - Default: `7.5`

- **`controlnet_conditioning_scale`** (`float`, _optional_):
  The scale of the ControlNet. Default value: `1`
  - Default: `1`

- **`control_guidance_start`** (`float`, _optional_)
  - Default: `0`
  - Range: `0` to `1`

- **`control_guidance_end`** (`float`, _optional_):
   Default value: `1`
  - Default: `1`
  - Range: `0` to `1`

- **`seed`** (`integer`, _optional_):
  Seed of the generated Image. It will be the same value of the one passed in the
  input or the randomly generated that was used in case none was passed.

- **`scheduler`** (`SchedulerEnum`, _optional_):
  Scheduler / sampler to use for the image denoising process. Default value: `"Euler"`
  - Default: `"Euler"`
  - Options: `"DPM++ Karras SDE"`, `"Euler"`

- **`num_inference_steps`** (`integer`, _optional_):
  Increasing the amount of steps tells Stable Diffusion that it should take more steps
  to generate your final result which can increase the amount of detail in your image. Default value: `40`
  - Default: `40`
  - Range: `0` to `80`

- **`image_size`** (`ImageSize | Enum`, _optional_):
  The size of the generated image. You can choose between some presets or
  custom height and width that **must be multiples of 8**. Default value: `square_hd`
  - Default: `"square_hd"`
  - One of: ImageSize | Enum



**Required Parameters Example**:

```json
{
  "image_url": "https://storage.googleapis.com/falserverless/illusion-examples/pattern.png",
  "prompt": "(masterpiece:1.4), (best quality), (detailed), Medieval village scene with busy streets and castle in the distance"
}
```

**Full Example**:

```json
{
  "image_url": "https://storage.googleapis.com/falserverless/illusion-examples/pattern.png",
  "prompt": "(masterpiece:1.4), (best quality), (detailed), Medieval village scene with busy streets and castle in the distance",
  "negative_prompt": "(worst quality, poor details:1.4), lowres, (artist name, signature, watermark:1.4), bad-artist-anime, bad_prompt_version2, bad-hands-5, ng_deepnegative_v1_75t",
  "guidance_scale": 7.5,
  "controlnet_conditioning_scale": 1,
  "control_guidance_end": 1,
  "scheduler": "Euler",
  "num_inference_steps": 40,
  "image_size": "square_hd"
}
```


### Output Schema

The API returns the following output format:

- **`image`** (`Image`, _required_):
  The generated image file info.

- **`seed`** (`integer`, _required_):
  Seed of the generated Image. It will be the same value of the one passed in the
  input or the randomly generated that was used in case none was passed.



**Example Response**:

```json
{
  "image": {
    "url": "",
    "content_type": "image/png",
    "file_name": "z9RV14K95DvU.png",
    "file_size": 4404019,
    "width": 1024,
    "height": 1024
  }
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/illusion-diffusion \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "image_url": "https://storage.googleapis.com/falserverless/illusion-examples/pattern.png",
     "prompt": "(masterpiece:1.4), (best quality), (detailed), Medieval village scene with busy streets and castle in the distance"
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
    "fal-ai/illusion-diffusion",
    arguments={
        "image_url": "https://storage.googleapis.com/falserverless/illusion-examples/pattern.png",
        "prompt": "(masterpiece:1.4), (best quality), (detailed), Medieval village scene with busy streets and castle in the distance"
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

const result = await fal.subscribe("fal-ai/illusion-diffusion", {
  input: {
    image_url: "https://storage.googleapis.com/falserverless/illusion-examples/pattern.png",
    prompt: "(masterpiece:1.4), (best quality), (detailed), Medieval village scene with busy streets and castle in the distance"
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

- [Model Playground](https://fal.ai/models/fal-ai/illusion-diffusion)
- [API Documentation](https://fal.ai/models/fal-ai/illusion-diffusion/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/illusion-diffusion)
- [GitHub Repository](https://huggingface.co/spaces/CompVis/stable-diffusion-license)

### fal.ai Platform

- [Platform Documentation](https://docs.fal.ai)
- [Python Client](https://docs.fal.ai/clients/python)
- [JavaScript Client](https://docs.fal.ai/clients/javascript)
