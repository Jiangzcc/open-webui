# Stable Diffusion V3

> Stable Diffusion 3 Medium (Image to Image) is a Multimodal Diffusion Transformer (MMDiT) model that improves image quality, typography, prompt understanding, and efficiency.


## Overview

- **Endpoint**: `https://fal.run/fal-ai/stable-diffusion-v3-medium/image-to-image`
- **Model ID**: `fal-ai/stable-diffusion-v3-medium/image-to-image`
- **Category**: image-to-image
- **Kind**: inference
**Tags**: diffusion, editing, style



## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`image_url`** (`string`, _required_):
  The image URL to generate an image from.
  - Examples: "https://fal.media/files/zebra/b52cVi3BhLDJcBrk6x0DL.png"

- **`prompt`** (`string`, _required_):
  The prompt to generate an image from.
  - Examples: "cat wizard, gandalf, lord of the rings, detailed, fantasy, cute, adorable, Pixar, Disney, 8k"

- **`negative_prompt`** (`string`, _optional_):
  The negative prompt to generate an image from. Default value: `""`
  - Default: `""`

- **`prompt_expansion`** (`boolean`, _optional_):
  If set to true, prompt will be upsampled with more details.
  - Default: `false`

- **`image_size`** (`ImageSize | Enum`, _optional_):
  The size of the generated image. Defaults to the conditioning image's size.
  - One of: ImageSize | Enum
  - Examples: null

- **`num_inference_steps`** (`integer`, _optional_):
  The number of inference steps to perform. Default value: `28`
  - Default: `28`
  - Range: `1` to `50`

- **`seed`** (`integer`, _optional_):
  The same seed and the same prompt given to the same version of Stable Diffusion
  will output the same image every time.

- **`guidance_scale`** (`float`, _optional_):
  The CFG (Classifier Free Guidance) scale is a measure of how close you want
  the model to stick to your prompt when looking for a related image to show you. Default value: `5`
  - Default: `5`
  - Range: `0` to `20`

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

- **`strength`** (`float`, _optional_):
  The strength of the image-to-image transformation. Default value: `0.9`
  - Default: `0.9`
  - Range: `0.01` to `1`



**Required Parameters Example**:

```json
{
  "image_url": "https://fal.media/files/zebra/b52cVi3BhLDJcBrk6x0DL.png",
  "prompt": "cat wizard, gandalf, lord of the rings, detailed, fantasy, cute, adorable, Pixar, Disney, 8k"
}
```

**Full Example**:

```json
{
  "image_url": "https://fal.media/files/zebra/b52cVi3BhLDJcBrk6x0DL.png",
  "prompt": "cat wizard, gandalf, lord of the rings, detailed, fantasy, cute, adorable, Pixar, Disney, 8k",
  "image_size": null,
  "num_inference_steps": 28,
  "guidance_scale": 5,
  "num_images": 1,
  "enable_safety_checker": true,
  "strength": 0.9
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

- **`num_images`** (`integer`, _required_):
  The number of images generated.



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
  --url https://fal.run/fal-ai/stable-diffusion-v3-medium/image-to-image \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "image_url": "https://fal.media/files/zebra/b52cVi3BhLDJcBrk6x0DL.png",
     "prompt": "cat wizard, gandalf, lord of the rings, detailed, fantasy, cute, adorable, Pixar, Disney, 8k"
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
    "fal-ai/stable-diffusion-v3-medium/image-to-image",
    arguments={
        "image_url": "https://fal.media/files/zebra/b52cVi3BhLDJcBrk6x0DL.png",
        "prompt": "cat wizard, gandalf, lord of the rings, detailed, fantasy, cute, adorable, Pixar, Disney, 8k"
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

const result = await fal.subscribe("fal-ai/stable-diffusion-v3-medium/image-to-image", {
  input: {
    image_url: "https://fal.media/files/zebra/b52cVi3BhLDJcBrk6x0DL.png",
    prompt: "cat wizard, gandalf, lord of the rings, detailed, fantasy, cute, adorable, Pixar, Disney, 8k"
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

- [Model Playground](https://fal.ai/models/fal-ai/stable-diffusion-v3-medium/image-to-image)
- [API Documentation](https://fal.ai/models/fal-ai/stable-diffusion-v3-medium/image-to-image/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/stable-diffusion-v3-medium/image-to-image)
- [GitHub Repository](https://huggingface.co/stabilityai/stable-diffusion-3-medium/blob/main/LICENSE)

### fal.ai Platform

- [Platform Documentation](https://docs.fal.ai)
- [Python Client](https://docs.fal.ai/clients/python)
- [JavaScript Client](https://docs.fal.ai/clients/javascript)
