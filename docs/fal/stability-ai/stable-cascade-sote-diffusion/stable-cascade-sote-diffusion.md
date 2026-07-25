# SoteDiffusion

> Anime finetune of Würstchen V3.


## Overview

- **Endpoint**: `https://fal.run/fal-ai/stable-cascade/sote-diffusion`
- **Model ID**: `fal-ai/stable-cascade/sote-diffusion`
- **Category**: text-to-image
- **Kind**: inference
**Tags**: lcm, stylized



## Pricing

- **Price**: $0 per compute seconds

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _required_):
  The prompt to use for generating the image. Be as descriptive as possible for best results.
  - Examples: "newest, extremely aesthetic, best quality, 1girl, solo, pink hair, blue eyes, long hair, looking at viewer, smile, black background, holding a sign, the text on the sign says \"Hello\""

- **`negative_prompt`** (`string`, _optional_):
  The negative prompt to use. Use it to address details that you don't want
  in the image. This could be colors, objects, scenery and even the small details
  (e.g. moustache, blurry, low resolution). Default value: `""`
  - Default: `""`
  - Examples: "very displeasing, worst quality, monochrome, realistic, oldest"

- **`first_stage_steps`** (`integer`, _optional_):
  Number of steps to run the first stage for. Default value: `25`
  - Default: `25`
  - Range: `4` to `50`

- **`second_stage_steps`** (`integer`, _optional_):
  Number of steps to run the second stage for. Default value: `10`
  - Default: `10`
  - Range: `4` to `24`

- **`guidance_scale`** (`float`, _optional_):
  The CFG (Classifier Free Guidance) scale is a measure of how close you want
  the model to stick to your prompt when looking for a related image to show you. Default value: `8`
  - Default: `8`
  - Range: `0` to `20`

- **`second_stage_guidance_scale`** (`float`, _optional_):
  The CFG (Classifier Free Guidance) scale is a measure of how close you want
  the model to stick to your prompt when looking for a related image to show you. Default value: `2`
  - Default: `2`
  - Range: `0` to `20`

- **`image_size`** (`ImageSize | Enum`, _optional_):
  The size of the generated image.
  - Default: `{"height":1536,"width":1024}`
  - One of: ImageSize | Enum

- **`seed`** (`integer`, _optional_):
  The same seed and the same prompt given to the same version of Stable Cascade
  will output the same image every time.

- **`enable_safety_checker`** (`boolean`, _optional_):
  If set to false, the safety checker will be disabled. Default value: `true`
  - Default: `true`

- **`num_images`** (`integer`, _optional_):
  The number of images to generate. Default value: `1`
  - Default: `1`
  - Range: `1` to `4`

- **`sync_mode`** (`boolean`, _optional_):
  If `True`, the media will be returned as a data URI and the output data won't be available in the request history.
  - Default: `false`



**Required Parameters Example**:

```json
{
  "prompt": "newest, extremely aesthetic, best quality, 1girl, solo, pink hair, blue eyes, long hair, looking at viewer, smile, black background, holding a sign, the text on the sign says \"Hello\""
}
```

**Full Example**:

```json
{
  "prompt": "newest, extremely aesthetic, best quality, 1girl, solo, pink hair, blue eyes, long hair, looking at viewer, smile, black background, holding a sign, the text on the sign says \"Hello\"",
  "negative_prompt": "very displeasing, worst quality, monochrome, realistic, oldest",
  "first_stage_steps": 25,
  "second_stage_steps": 10,
  "guidance_scale": 8,
  "second_stage_guidance_scale": 2,
  "image_size": {
    "height": 1536,
    "width": 1024
  },
  "enable_safety_checker": true,
  "num_images": 1
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
  --url https://fal.run/fal-ai/stable-cascade/sote-diffusion \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "newest, extremely aesthetic, best quality, 1girl, solo, pink hair, blue eyes, long hair, looking at viewer, smile, black background, holding a sign, the text on the sign says \"Hello\""
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
    "fal-ai/stable-cascade/sote-diffusion",
    arguments={
        "prompt": "newest, extremely aesthetic, best quality, 1girl, solo, pink hair, blue eyes, long hair, looking at viewer, smile, black background, holding a sign, the text on the sign says \"Hello\""
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

const result = await fal.subscribe("fal-ai/stable-cascade/sote-diffusion", {
  input: {
    prompt: "newest, extremely aesthetic, best quality, 1girl, solo, pink hair, blue eyes, long hair, looking at viewer, smile, black background, holding a sign, the text on the sign says \"Hello\""
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

- [Model Playground](https://fal.ai/models/fal-ai/stable-cascade/sote-diffusion)
- [API Documentation](https://fal.ai/models/fal-ai/stable-cascade/sote-diffusion/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/stable-cascade/sote-diffusion)
- [GitHub Repository](https://huggingface.co/stabilityai/stable-cascade/blob/main/LICENSE)

### fal.ai Platform

- [Platform Documentation](https://docs.fal.ai)
- [Python Client](https://docs.fal.ai/clients/python)
- [JavaScript Client](https://docs.fal.ai/clients/javascript)
