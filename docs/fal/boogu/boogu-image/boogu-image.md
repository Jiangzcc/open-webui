# Boogu Image

> Text To Image Model using Boogu-Image


## Overview

- **Endpoint**: `https://fal.run/fal-ai/boogu-image`
- **Model ID**: `fal-ai/boogu-image`
- **Category**: text-to-image
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
  The instruction describing the image to generate. Boogu-Image is bilingual — English and Chinese instructions are both supported. Detailed, descriptive prompts produce the best results.
  - Examples: "A street photography shot of an elderly scavenger with a deeply weathered face in the center of the frame, a trash can and a traffic light in the background. Shot on a Leica camera, high photographic texture, cinematic lighting, photorealistic.", "一只柯基犬戴着墨镜，坐在阳光明媚的海滩上，电影感，浅景深。"

- **`negative_prompt`** (`string`, _optional_):
  Describes what should NOT appear in the image. Used for classifier-free guidance; leave empty to disable text negative guidance. Default value: `""`
  - Default: `""`

- **`image_size`** (`ImageSize | Enum`, _optional_):
  The size of the generated image. The model's maximum native resolution is 2K; larger requests are clamped. Dimensions are aligned to multiples of 16. Default value: `square_hd`
  - Default: `"square_hd"`
  - One of: ImageSize | Enum

- **`num_inference_steps`** (`integer`, _optional_):
  The number of denoising steps to perform. Default value: `30`
  - Default: `30`
  - Range: `20` to `50`

- **`guidance_scale`** (`float`, _optional_):
  Controls how closely generation follows the text instruction. Higher values stick more closely to the prompt. A value of 1.0 disables text classifier-free guidance. Default value: `4`
  - Default: `4`
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
  The number of images to generate. Default value: `1`
  - Default: `1`
  - Range: `1` to `4`

- **`seed`** (`integer`, _optional_):
  The same seed and the same prompt given to the same version of the model will output the same image every time.

- **`enable_safety_checker`** (`boolean`, _optional_):
  If true, the safety checker is run on the generated images. Default value: `true`
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
  "prompt": "A street photography shot of an elderly scavenger with a deeply weathered face in the center of the frame, a trash can and a traffic light in the background. Shot on a Leica camera, high photographic texture, cinematic lighting, photorealistic."
}
```

**Full Example**:

```json
{
  "prompt": "A street photography shot of an elderly scavenger with a deeply weathered face in the center of the frame, a trash can and a traffic light in the background. Shot on a Leica camera, high photographic texture, cinematic lighting, photorealistic.",
  "image_size": "square_hd",
  "num_inference_steps": 30,
  "guidance_scale": 4,
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
  --url https://fal.run/fal-ai/boogu-image \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "A street photography shot of an elderly scavenger with a deeply weathered face in the center of the frame, a trash can and a traffic light in the background. Shot on a Leica camera, high photographic texture, cinematic lighting, photorealistic."
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
    "fal-ai/boogu-image",
    arguments={
        "prompt": "A street photography shot of an elderly scavenger with a deeply weathered face in the center of the frame, a trash can and a traffic light in the background. Shot on a Leica camera, high photographic texture, cinematic lighting, photorealistic."
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

const result = await fal.subscribe("fal-ai/boogu-image", {
  input: {
    prompt: "A street photography shot of an elderly scavenger with a deeply weathered face in the center of the frame, a trash can and a traffic light in the background. Shot on a Leica camera, high photographic texture, cinematic lighting, photorealistic."
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

- [Model Playground](https://fal.ai/models/fal-ai/boogu-image)
- [API Documentation](https://fal.ai/models/fal-ai/boogu-image/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/boogu-image)

### fal.ai Platform

- [Platform Documentation](https://docs.fal.ai)
- [Python Client](https://docs.fal.ai/clients/python)
- [JavaScript Client](https://docs.fal.ai/clients/javascript)
