# Bernini-R Text to Video

> Generate high-quality video from a text prompt with Bernini-R, ByteDance's unified video generation and editing model.


## Overview

- **Endpoint**: `https://fal.run/fal-ai/bernini-r/text-to-video`
- **Model ID**: `fal-ai/bernini-r/text-to-video`
- **Category**: text-to-video
- **Kind**: inference
**Description**: Bernini R turns a text prompt into a high-quality video. It is ByteDance's unified model for generating and editing video, so the same family that restyles and edits clips also generates them from scratch with strong prompt control.

**Tags**: text-to-video, cinematic



## Pricing

For every second of 848px (default) video you generated, you will be charged $0.08/second. Your request will be scaled by resolution along the longest edge. The scaling multiplier is given by 0.5 for ≤576px, 1 for 848px, and 2 for 1280px.

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _required_):
  Text prompt or editing instruction.
  - Examples: "A cute corgi leaping in a sunny park, Van Gogh oil-painting style."

- **`negative_prompt`** (`string`, _optional_):
  Negative prompt. Defaults to the standard Wan2.2 negative prompt.

- **`num_inference_steps`** (`integer`, _optional_):
  Number of denoising steps. Default value: `30`
  - Default: `30`
  - Range: `1` to `50`

- **`max_image_size`** (`integer`, _optional_):
  Long-edge size (px). Sets the output size for generation tasks and caps source/reference media for editing tasks. Default value: `848`
  - Default: `848`
  - Range: `256` to `1280`

- **`seed`** (`integer`, _optional_):
  Seed for reproducibility. Random when omitted.

- **`enable_prompt_expansion`** (`boolean`, _optional_):
  Rewrite the prompt with an LLM before generation. The model is tuned on enhanced prompts; off by default.
  - Default: `false`

- **`num_frames`** (`integer`, _optional_):
  Number of frames. Snapped internally to 4k+1. Default value: `81`
  - Default: `81`
  - Range: `5` to `121`

- **`frames_per_second`** (`integer`, _optional_):
  Output frames per second. Default value: `16`
  - Default: `16`
  - Range: `4` to `30`

- **`acceleration`** (`AccelerationEnum`, _optional_):
  Acceleration level. 'regular' enables MagCache step-skipping for faster generation at a small quality cost; 'none' (default) runs the full denoising schedule. Default value: `"none"`
  - Default: `"none"`
  - Options: `"none"`, `"regular"`

- **`aspect_ratio`** (`AspectRatioEnum`, _optional_):
  Output aspect ratio. Default value: `"16:9"`
  - Default: `"16:9"`
  - Options: `"16:9"`, `"9:16"`, `"1:1"`



**Required Parameters Example**:

```json
{
  "prompt": "A cute corgi leaping in a sunny park, Van Gogh oil-painting style."
}
```

**Full Example**:

```json
{
  "prompt": "A cute corgi leaping in a sunny park, Van Gogh oil-painting style.",
  "num_inference_steps": 30,
  "max_image_size": 848,
  "num_frames": 81,
  "frames_per_second": 16,
  "acceleration": "none",
  "aspect_ratio": "16:9"
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`File`, _required_):
  Generated / edited video.

- **`seed`** (`integer`, _required_):
  Seed used for generation.

- **`actual_prompt`** (`string`, _optional_):
  The final prompt after expansion (set only when prompt expansion ran).



**Example Response**:

```json
{
  "video": {
    "url": "",
    "content_type": "image/png",
    "file_name": "z9RV14K95DvU.png",
    "file_size": 4404019
  }
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/bernini-r/text-to-video \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "A cute corgi leaping in a sunny park, Van Gogh oil-painting style."
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
    "fal-ai/bernini-r/text-to-video",
    arguments={
        "prompt": "A cute corgi leaping in a sunny park, Van Gogh oil-painting style."
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

const result = await fal.subscribe("fal-ai/bernini-r/text-to-video", {
  input: {
    prompt: "A cute corgi leaping in a sunny park, Van Gogh oil-painting style."
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

- [Model Playground](https://fal.ai/models/fal-ai/bernini-r/text-to-video)
- [API Documentation](https://fal.ai/models/fal-ai/bernini-r/text-to-video/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/bernini-r/text-to-video)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
