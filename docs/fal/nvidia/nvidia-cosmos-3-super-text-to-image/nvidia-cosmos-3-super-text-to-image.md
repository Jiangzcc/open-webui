# Cosmos 3 Super

> Cosmos3 is a collection of Omnimodal world models capable of generating dynamic, high-quality video, image, audio, and action commands from combinations of text, image, video, and action trajectory inputs.


## Overview

- **Endpoint**: `https://fal.run/nvidia/cosmos-3-super/text-to-image`
- **Model ID**: `nvidia/cosmos-3-super/text-to-image`
- **Category**: text-to-image
- **Kind**: inference
**Tags**: stylized, transform, realism



## Pricing

Your request will cost **$0.04** per generated image. Prompt expansion adds **$0.02** per request when enabled. Agentic generation bills for every candidate image generated during selection, not just the final returned image.

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _required_):
  Text prompt describing the image to generate.
  - Examples: "A photorealistic close-up of two damp hands shaping a spinning cylinder of wet gray clay on a pottery wheel, fingers pinching the walls upward into a narrow-necked vase, water glistening on the clay, soft studio lighting, shallow depth of field."

- **`negative_prompt`** (`string`, _optional_):
  Content to steer the generation away from (colors, objects, artifacts). Default value: `""`
  - Default: `""`
  - Examples: ""

- **`enable_prompt_expansion`** (`boolean`, _optional_):
  Expand the prompt with OpenRouter before image generation. When enabled, the prompt is rewritten into the dense structured-JSON format Cosmos3 was trained on; generation falls back to the raw prompt if expansion fails.
  - Default: `false`

- **`enable_agentic_generation`** (`boolean`, _optional_):
  Automatically generate and compare multiple candidate images, then refine the prompt between rounds to better match the original request. This can improve prompt adherence but increases latency and billable image generations.
  - Default: `false`

- **`agentic_max_iterations`** (`integer`, _optional_):
  Maximum number of refinement rounds when agentic generation is enabled. Default value: `2`
  - Default: `2`
  - Range: `1` to `3`

- **`agentic_samples_per_iteration`** (`integer`, _optional_):
  Candidate images to generate and judge per agentic iteration. The best candidate advances to the next rewrite stage. Default value: `2`
  - Default: `2`
  - Range: `1` to `3`

- **`agentic_early_stop`** (`boolean`, _optional_):
  Stop early when a candidate image is already a strong match for the prompt. Default value: `true`
  - Default: `true`

- **`image_size`** (`ImageSize | Enum`, _optional_):
  The size of the generated image. Each edge is clamped to 512-1280px (multiples of 16). Default value: `square_hd`
  - Default: `"square_hd"`
  - One of: ImageSize | Enum
  - Examples: {"width":1024,"height":1024}

- **`num_inference_steps`** (`integer`, _optional_):
  Number of denoising steps. More steps yield higher quality but take longer. Default value: `28`
  - Default: `28`
  - Range: `1` to `50`

- **`guidance_scale`** (`float`, _optional_):
  Classifier-free guidance scale. Higher values increase prompt adherence at the cost of diversity. Default value: `4`
  - Default: `4`
  - Range: `0` to `20`

- **`num_images`** (`integer`, _optional_):
  The number of images to generate. Default value: `1`
  - Default: `1`
  - Range: `1` to `4`

- **`seed`** (`integer`, _optional_):
  The same seed and prompt given to the same model version will produce the same image every time.

- **`enable_safety_checker`** (`boolean`, _optional_):
  Enable content moderation for the input prompt and generated images. Default value: `true`
  - Default: `true`

- **`sync_mode`** (`boolean`, _optional_):
  If `True`, the image is returned as a data URI and the output data won't be available in the request history.
  - Default: `false`

- **`output_format`** (`OutputFormatEnum`, _optional_):
  The format of the generated image. Default value: `"jpeg"`
  - Default: `"jpeg"`
  - Options: `"jpeg"`, `"png"`



**Required Parameters Example**:

```json
{
  "prompt": "A photorealistic close-up of two damp hands shaping a spinning cylinder of wet gray clay on a pottery wheel, fingers pinching the walls upward into a narrow-necked vase, water glistening on the clay, soft studio lighting, shallow depth of field."
}
```

**Full Example**:

```json
{
  "prompt": "A photorealistic close-up of two damp hands shaping a spinning cylinder of wet gray clay on a pottery wheel, fingers pinching the walls upward into a narrow-necked vase, water glistening on the clay, soft studio lighting, shallow depth of field.",
  "negative_prompt": "",
  "agentic_max_iterations": 2,
  "agentic_samples_per_iteration": 2,
  "agentic_early_stop": true,
  "image_size": {
    "width": 1024,
    "height": 1024
  },
  "num_inference_steps": 28,
  "guidance_scale": 4,
  "num_images": 1,
  "enable_safety_checker": true,
  "output_format": "jpeg"
}
```


### Output Schema

The API returns the following output format:

- **`images`** (`list<ImageFile>`, _required_):
  The generated images.
  - Array of ImageFile
  - Examples: [{"file_name":"cosmos3-vllm-example.jpeg","content_type":"image/jpeg","url":"https://v3b.fal.media/files/b/0a8fc99c/cosmos3-vllm-example.jpeg"}]

- **`seed`** (`integer`, _required_):
  The seed used for generation.
  - Examples: 1143

- **`has_nsfw_concepts`** (`list<boolean>`, _required_):
  Whether each generated image was flagged by the safety checker.
  - Array of boolean
  - Examples: [false]



**Example Response**:

```json
{
  "images": [
    {
      "file_name": "cosmos3-vllm-example.jpeg",
      "content_type": "image/jpeg",
      "url": "https://v3b.fal.media/files/b/0a8fc99c/cosmos3-vllm-example.jpeg"
    }
  ],
  "seed": 1143,
  "has_nsfw_concepts": [
    false
  ]
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/nvidia/cosmos-3-super/text-to-image \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "A photorealistic close-up of two damp hands shaping a spinning cylinder of wet gray clay on a pottery wheel, fingers pinching the walls upward into a narrow-necked vase, water glistening on the clay, soft studio lighting, shallow depth of field."
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
    "nvidia/cosmos-3-super/text-to-image",
    arguments={
        "prompt": "A photorealistic close-up of two damp hands shaping a spinning cylinder of wet gray clay on a pottery wheel, fingers pinching the walls upward into a narrow-necked vase, water glistening on the clay, soft studio lighting, shallow depth of field."
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

const result = await fal.subscribe("nvidia/cosmos-3-super/text-to-image", {
  input: {
    prompt: "A photorealistic close-up of two damp hands shaping a spinning cylinder of wet gray clay on a pottery wheel, fingers pinching the walls upward into a narrow-necked vase, water glistening on the clay, soft studio lighting, shallow depth of field."
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

- [Model Playground](https://fal.ai/models/nvidia/cosmos-3-super/text-to-image)
- [API Documentation](https://fal.ai/models/nvidia/cosmos-3-super/text-to-image/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=nvidia/cosmos-3-super/text-to-image)

### fal.ai Platform

- [Platform Documentation](https://docs.fal.ai)
- [Python Client](https://docs.fal.ai/clients/python)
- [JavaScript Client](https://docs.fal.ai/clients/javascript)
