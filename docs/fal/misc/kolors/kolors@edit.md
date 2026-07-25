# Kolors Image to Image

> Photorealistic Image-to-Image


## Overview

- **Endpoint**: `https://fal.run/fal-ai/kolors/image-to-image`
- **Model ID**: `fal-ai/kolors/image-to-image`
- **Category**: image-to-image
- **Kind**: inference
**Tags**: realism, editing, diffusion



## Pricing

- **Price**: $0 per compute seconds

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _required_):
  The prompt to generate an image from.
  - Examples: "high quality image of a capybara wearing sunglasses. In the background of the image there are trees, poles, grass and other objects. At the bottom of the object there is the road., 8k, highly detailed."

- **`negative_prompt`** (`string`, _optional_):
  The negative prompt to use. Use it to address details that you don't want
  in the image. This could be colors, objects, scenery and even the small
  details (e.g. moustache, blurry, low resolution). Default value: `""`
  - Default: `""`
  - Examples: "ugly, deformed, blurry"

- **`guidance_scale`** (`float`, _optional_):
  The CFG (Classifier Free Guidance) scale is a measure of how close you want
  the model to stick to your prompt when looking for a related image to show
  you. Default value: `5`
  - Default: `5`
  - Range: `1` to `10`

- **`num_inference_steps`** (`integer`, _optional_):
  The number of inference steps to perform. Default value: `50`
  - Default: `50`
  - Range: `1` to `150`

- **`seed`** (`integer`, _optional_):
  Seed

- **`sync_mode`** (`boolean`, _optional_):
  If `True`, the media will be returned as a data URI and the output data won't be available in the request history.
  - Default: `false`

- **`enable_safety_checker`** (`boolean`, _optional_):
  Enable safety checker. Default value: `true`
  - Default: `true`

- **`num_images`** (`integer`, _optional_):
  The number of images to generate. Default value: `1`
  - Default: `1`
  - Range: `1` to `8`

- **`image_size`** (`ImageSize | Enum`, _optional_):
  The size of the generated image.
  - One of: ImageSize | Enum

- **`scheduler`** (`SchedulerEnum`, _optional_):
  The scheduler to use for the model. Default value: `"EulerDiscreteScheduler"`
  - Default: `"EulerDiscreteScheduler"`
  - Options: `"EulerDiscreteScheduler"`, `"EulerAncestralDiscreteScheduler"`, `"DPMSolverMultistepScheduler"`, `"DPMSolverMultistepScheduler_SDE_karras"`, `"UniPCMultistepScheduler"`, `"DEISMultistepScheduler"`

- **`output_format`** (`OutputFormatEnum`, _optional_):
  The format of the generated image. Default value: `"png"`
  - Default: `"png"`
  - Options: `"jpeg"`, `"png"`

- **`image_url`** (`string`, _required_):
  URL of image to use for image to image
  - Examples: "https://storage.googleapis.com/falserverless/model_tests/image_models/bunny_source.png"

- **`strength`** (`float`, _optional_):
  The strength to use for image-to-image. 1.0 is completely remakes the image while 0.0 preserves the original. Default value: `0.85`
  - Default: `0.85`
  - Range: `0.01` to `1`



**Required Parameters Example**:

```json
{
  "prompt": "high quality image of a capybara wearing sunglasses. In the background of the image there are trees, poles, grass and other objects. At the bottom of the object there is the road., 8k, highly detailed.",
  "image_url": "https://storage.googleapis.com/falserverless/model_tests/image_models/bunny_source.png"
}
```

**Full Example**:

```json
{
  "prompt": "high quality image of a capybara wearing sunglasses. In the background of the image there are trees, poles, grass and other objects. At the bottom of the object there is the road., 8k, highly detailed.",
  "negative_prompt": "ugly, deformed, blurry",
  "guidance_scale": 5,
  "num_inference_steps": 50,
  "enable_safety_checker": true,
  "num_images": 1,
  "scheduler": "EulerDiscreteScheduler",
  "output_format": "png",
  "image_url": "https://storage.googleapis.com/falserverless/model_tests/image_models/bunny_source.png",
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
  --url https://fal.run/fal-ai/kolors/image-to-image \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "high quality image of a capybara wearing sunglasses. In the background of the image there are trees, poles, grass and other objects. At the bottom of the object there is the road., 8k, highly detailed.",
     "image_url": "https://storage.googleapis.com/falserverless/model_tests/image_models/bunny_source.png"
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
    "fal-ai/kolors/image-to-image",
    arguments={
        "prompt": "high quality image of a capybara wearing sunglasses. In the background of the image there are trees, poles, grass and other objects. At the bottom of the object there is the road., 8k, highly detailed.",
        "image_url": "https://storage.googleapis.com/falserverless/model_tests/image_models/bunny_source.png"
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

const result = await fal.subscribe("fal-ai/kolors/image-to-image", {
  input: {
    prompt: "high quality image of a capybara wearing sunglasses. In the background of the image there are trees, poles, grass and other objects. At the bottom of the object there is the road., 8k, highly detailed.",
    image_url: "https://storage.googleapis.com/falserverless/model_tests/image_models/bunny_source.png"
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

- [Model Playground](https://fal.ai/models/fal-ai/kolors/image-to-image)
- [API Documentation](https://fal.ai/models/fal-ai/kolors/image-to-image/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/kolors/image-to-image)
- [GitHub Repository](https://huggingface.co/Kwai-Kolors/Kolors-diffusers/raw/main/MODEL_LICENSE)

### fal.ai Platform

- [Platform Documentation](https://docs.fal.ai)
- [Python Client](https://docs.fal.ai/clients/python)
- [JavaScript Client](https://docs.fal.ai/clients/javascript)
