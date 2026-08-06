# Sensenova U1 Infographic

> Generate Infographic Image with Sensenova U1


## Overview

- **Endpoint**: `https://fal.run/fal-ai/sensenova-u1-infographic`
- **Model ID**: `fal-ai/sensenova-u1-infographic`
- **Category**: text-to-image
- **Kind**: inference


## Pricing

  Your request will cost **$0.05** per generated image. Enabling thinking mode applies a 1.2x multiplier, so a request with thinking mode will cost **$0.06** per image.

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _required_):
  Text prompt describing the infographic to generate. Detailed prompts that specify layout, sections, color palette, typography, and the data being visualized work best.
  - Examples: "A flat-design infographic titled 'The Lifecycle of a Tree' with five labeled stages laid out left-to-right (seed, sapling, young tree, mature tree, decomposition), soft pastel green-and-brown palette, minimal sans-serif headings, hand-drawn vector illustrations, white background, subtle drop-shadow on cards."

- **`aspect_ratio`** (`AspectRatioEnum`, _optional_):
  Aspect ratio for the generated image. Maps to the trained resolution buckets — using ratios outside this set is not supported. Defaults to 16:9, which fits most poster / presentation-style infographics. Default value: `"16:9"`
  - Default: `"16:9"`
  - Options: `"1:1"`, `"16:9"`, `"9:16"`, `"3:2"`, `"2:3"`, `"4:3"`, `"3:4"`, `"1:2"`, `"2:1"`

- **`num_inference_steps`** (`integer`, _optional_):
  Number of flow-matching denoising steps. Default value: `50`
  - Default: `50`
  - Range: `10` to `100`

- **`guidance_scale`** (`float`, _optional_):
  Classifier-free guidance scale. Higher values follow the prompt more strictly. Default value: `4`
  - Default: `4`
  - Range: `1` to `10`

- **`timestep_shift`** (`float`, _optional_):
  Timestep shifting factor for the flow-matching sampler. Higher values bias sampling towards earlier timesteps. Default value: `3`
  - Default: `3`
  - Range: `1` to `8`

- **`use_thinking`** (`boolean`, _optional_):
  If True, run chain-of-thought before image generation. Improves complex-prompt fidelity but is slower and billed at 1.2x.
  - Default: `false`

- **`seed`** (`integer`, _optional_):
  The same seed and the same prompt given to the same version of the model will output the same image every time.

- **`enable_safety_checker`** (`boolean`, _optional_):
  If set to true, the safety checker will be enabled. Default value: `true`
  - Default: `true`

- **`output_format`** (`OutputFormatEnum`, _optional_):
  The format of the generated image. Default value: `"jpeg"`
  - Default: `"jpeg"`
  - Options: `"jpeg"`, `"png"`

- **`sync_mode`** (`boolean`, _optional_):
  If True, the media will be returned as a data URI and the output data won't be available in the request history.
  - Default: `false`



**Required Parameters Example**:

```json
{
  "prompt": "A flat-design infographic titled 'The Lifecycle of a Tree' with five labeled stages laid out left-to-right (seed, sapling, young tree, mature tree, decomposition), soft pastel green-and-brown palette, minimal sans-serif headings, hand-drawn vector illustrations, white background, subtle drop-shadow on cards."
}
```

**Full Example**:

```json
{
  "prompt": "A flat-design infographic titled 'The Lifecycle of a Tree' with five labeled stages laid out left-to-right (seed, sapling, young tree, mature tree, decomposition), soft pastel green-and-brown palette, minimal sans-serif headings, hand-drawn vector illustrations, white background, subtle drop-shadow on cards.",
  "aspect_ratio": "16:9",
  "num_inference_steps": 50,
  "guidance_scale": 4,
  "timestep_shift": 3,
  "enable_safety_checker": true,
  "output_format": "jpeg"
}
```


### Output Schema

The API returns the following output format:

- **`images`** (`list<Image>`, _required_):
  The generated image(s).
  - Array of Image

- **`seed`** (`integer`, _required_):
  The seed used for the generation.

- **`has_nsfw_concepts`** (`list<boolean>`, _required_):
  Whether the generated images contain NSFW concepts.
  - Array of boolean

- **`prompt`** (`string`, _required_):
  The prompt used for the generation.

- **`thinking`** (`string`, _optional_):
  Chain-of-thought trace emitted when ``use_thinking`` is True, else ``null``.

- **`timings`** (`Timings`, _required_):
  Per-stage timings in seconds.



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
  --url https://fal.run/fal-ai/sensenova-u1-infographic \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "A flat-design infographic titled 'The Lifecycle of a Tree' with five labeled stages laid out left-to-right (seed, sapling, young tree, mature tree, decomposition), soft pastel green-and-brown palette, minimal sans-serif headings, hand-drawn vector illustrations, white background, subtle drop-shadow on cards."
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
    "fal-ai/sensenova-u1-infographic",
    arguments={
        "prompt": "A flat-design infographic titled 'The Lifecycle of a Tree' with five labeled stages laid out left-to-right (seed, sapling, young tree, mature tree, decomposition), soft pastel green-and-brown palette, minimal sans-serif headings, hand-drawn vector illustrations, white background, subtle drop-shadow on cards."
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

const result = await fal.subscribe("fal-ai/sensenova-u1-infographic", {
  input: {
    prompt: "A flat-design infographic titled 'The Lifecycle of a Tree' with five labeled stages laid out left-to-right (seed, sapling, young tree, mature tree, decomposition), soft pastel green-and-brown palette, minimal sans-serif headings, hand-drawn vector illustrations, white background, subtle drop-shadow on cards."
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

- [Model Playground](https://fal.ai/models/fal-ai/sensenova-u1-infographic)
- [API Documentation](https://fal.ai/models/fal-ai/sensenova-u1-infographic/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/sensenova-u1-infographic)

### fal.ai Platform

- [Platform Documentation](https://docs.fal.ai)
- [Python Client](https://docs.fal.ai/clients/python)
- [JavaScript Client](https://docs.fal.ai/clients/javascript)
