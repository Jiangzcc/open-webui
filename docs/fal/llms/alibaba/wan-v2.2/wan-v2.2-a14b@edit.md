# Wan

> Wan 2.2's 14B model edit high-resolution, photorealistic images with powerful prompt understanding and fine-grained visual detail


## Overview

- **Endpoint**: `https://fal.run/fal-ai/wan/v2.2-a14b/image-to-image`
- **Model ID**: `fal-ai/wan/v2.2-a14b/image-to-image`
- **Category**: image-to-image
- **Kind**: inference
**Tags**: image-to-image



## Pricing

- **Price**: $0.05 per images

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`image_url`** (`string`, _required_):
  URL of the input image.
  - Examples: "https://storage.googleapis.com/falserverless/example_inputs/wan-image-to-image-input.png"

- **`prompt`** (`string`, _required_):
  The text prompt to guide image generation.
  - Examples: "A cinematic shot of an ancient city at sunset, intricate stone buildings, warm golden light"

- **`strength`** (`float`, _optional_):
  Denoising strength. 1.0 = fully remake; 0.0 = preserve original. Default value: `0.5`
  - Default: `0.5`
  - Range: `0` to `1`

- **`negative_prompt`** (`string`, _optional_):
  Negative prompt for video generation. Default value: `""`
  - Default: `""`

- **`seed`** (`integer`, _optional_):
  Random seed for reproducibility. If None, a random seed is chosen.

- **`aspect_ratio`** (`AspectRatioEnum`, _optional_):
  Aspect ratio of the generated image. If 'auto', the aspect ratio will be determined automatically based on the input image. Default value: `"auto"`
  - Default: `"auto"`
  - Options: `"auto"`, `"16:9"`, `"9:16"`, `"1:1"`

- **`num_inference_steps`** (`integer`, _optional_):
  Number of inference steps for sampling. Higher values give better quality but take longer. Default value: `27`
  - Default: `27`
  - Range: `2` to `40`
  - Examples: 27

- **`enable_safety_checker`** (`boolean`, _optional_):
  If set to true, input data will be checked for safety before processing.
  - Default: `false`
  - Examples: true

- **`enable_output_safety_checker`** (`boolean`, _optional_):
  If set to true, output video will be checked for safety after generation.
  - Default: `false`
  - Examples: false

- **`enable_prompt_expansion`** (`boolean`, _optional_):
  Whether to enable prompt expansion. This will use a large language model to expand the prompt with additional details while maintaining the original meaning.
  - Default: `false`
  - Examples: false

- **`acceleration`** (`AccelerationEnum`, _optional_):
  Acceleration level to use. The more acceleration, the faster the generation, but with lower quality. The recommended value is 'regular'. Default value: `"regular"`
  - Default: `"regular"`
  - Options: `"none"`, `"regular"`
  - Examples: "regular"

- **`guidance_scale`** (`float`, _optional_):
  Classifier-free guidance scale. Default value: `3.5`
  - Default: `3.5`
  - Range: `1` to `10`

- **`guidance_scale_2`** (`float`, _optional_):
  Guidance scale for the second stage of the model. This is used to control the adherence to the prompt in the second stage of the model. Default value: `4`
  - Default: `4`
  - Range: `1` to `10`
  - Examples: 4

- **`shift`** (`float`, _optional_):
   Default value: `2`
  - Default: `2`
  - Range: `1` to `10`

- **`image_size`** (`ImageSize | Enum`, _optional_)
  - One of: ImageSize | Enum

- **`image_format`** (`ImageFormatEnum`, _optional_):
  The format of the output image. Default value: `"jpeg"`
  - Default: `"jpeg"`
  - Options: `"png"`, `"jpeg"`
  - Examples: "jpeg"



**Required Parameters Example**:

```json
{
  "image_url": "https://storage.googleapis.com/falserverless/example_inputs/wan-image-to-image-input.png",
  "prompt": "A cinematic shot of an ancient city at sunset, intricate stone buildings, warm golden light"
}
```

**Full Example**:

```json
{
  "image_url": "https://storage.googleapis.com/falserverless/example_inputs/wan-image-to-image-input.png",
  "prompt": "A cinematic shot of an ancient city at sunset, intricate stone buildings, warm golden light",
  "strength": 0.5,
  "aspect_ratio": "auto",
  "num_inference_steps": 27,
  "enable_safety_checker": true,
  "enable_output_safety_checker": false,
  "enable_prompt_expansion": false,
  "acceleration": "regular",
  "guidance_scale": 3.5,
  "guidance_scale_2": 4,
  "shift": 2,
  "image_format": "jpeg"
}
```


### Output Schema

The API returns the following output format:

- **`image`** (`File`, _required_):
  The generated image file.
  - Examples: {"url":"https://storage.googleapis.com/falserverless/example_outputs/wan-image-to-image-output.png"}

- **`prompt`** (`string`, _optional_):
  The text prompt used for image generation. Default value: `""`
  - Default: `""`
  - Examples: "A cinematic portrait of a woman in natural light, 85mm look."

- **`seed`** (`integer`, _required_):
  The seed used for generation.



**Example Response**:

```json
{
  "image": {
    "url": "https://storage.googleapis.com/falserverless/example_outputs/wan-image-to-image-output.png"
  },
  "prompt": "A cinematic portrait of a woman in natural light, 85mm look."
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/wan/v2.2-a14b/image-to-image \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "image_url": "https://storage.googleapis.com/falserverless/example_inputs/wan-image-to-image-input.png",
     "prompt": "A cinematic shot of an ancient city at sunset, intricate stone buildings, warm golden light"
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
    "fal-ai/wan/v2.2-a14b/image-to-image",
    arguments={
        "image_url": "https://storage.googleapis.com/falserverless/example_inputs/wan-image-to-image-input.png",
        "prompt": "A cinematic shot of an ancient city at sunset, intricate stone buildings, warm golden light"
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

const result = await fal.subscribe("fal-ai/wan/v2.2-a14b/image-to-image", {
  input: {
    image_url: "https://storage.googleapis.com/falserverless/example_inputs/wan-image-to-image-input.png",
    prompt: "A cinematic shot of an ancient city at sunset, intricate stone buildings, warm golden light"
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

- [Model Playground](https://fal.ai/models/fal-ai/wan/v2.2-a14b/image-to-image)
- [API Documentation](https://fal.ai/models/fal-ai/wan/v2.2-a14b/image-to-image/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/wan/v2.2-a14b/image-to-image)

### fal.ai Platform

- [Platform Documentation](https://docs.fal.ai)
- [Python Client](https://docs.fal.ai/clients/python)
- [JavaScript Client](https://docs.fal.ai/clients/javascript)
