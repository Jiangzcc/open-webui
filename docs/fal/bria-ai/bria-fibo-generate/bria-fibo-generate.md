# Fibo

> SOTA open-source text-to-image model delivering high-fidelity outputs with accurate typography. JSON-structured prompts provide production-ready controllability for enterprise and agentic workflows. Trained exclusively on licensed data.


## Overview

- **Endpoint**: `https://fal.run/bria/fibo/generate`
- **Model ID**: `bria/fibo/generate`
- **Category**: text-to-image
- **Kind**: inference
**Description**: SOTA open-source text-to-image model delivering high-fidelity outputs with accurate typography. JSON-structured prompts provide production-ready controllability for enterprise and agentic workflows. Trained exclusively on licensed data.

**Tags**: bria, fibo, prompt-adherence



## Pricing

- **Price**: $0.04 per images

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _optional_):
  Prompt for image generation.
  - Examples: "A hyper-detailed, ultra-fluffy owl sitting in the trees at night, looking directly at the camera with wide, adorable, expressive eyes. Its feathers are soft and voluminous, catching the cool moonlight with subtle silver highlights. The owl’s gaze is curious and full of charm, giving it a whimsical, storybook-like personality."

- **`structured_prompt`** (`TailoredStructuredPrompt`, _optional_):
  The structured prompt to generate an image from.

- **`image_url`** (`string`, _optional_):
  Reference image (file or URL).

- **`seed`** (`integer`, _optional_):
  Random seed for reproducibility. Default value: `5555`
  - Default: `5555`

- **`steps_num`** (`integer`, _optional_):
  Number of inference steps. Default value: `50`
  - Default: `50`
  - Range: `20` to `50`

- **`aspect_ratio`** (`AspectRatioEnum`, _optional_):
  Aspect ratio. Options: 1:1, 2:3, 3:2, 3:4, 4:3, 4:5, 5:4, 9:16, 16:9 Default value: `"1:1"`
  - Default: `"1:1"`
  - Options: `"1:1"`, `"2:3"`, `"3:2"`, `"3:4"`, `"4:3"`, `"4:5"`, `"5:4"`, `"9:16"`, `"16:9"`

- **`negative_prompt`** (`string`, _optional_):
  Negative prompt for image generation. Default value: `""`
  - Default: `""`

- **`resolution`** (`ResolutionEnum`, _optional_):
  Output image resolution Default value: `"1MP"`
  - Default: `"1MP"`
  - Options: `"1MP"`, `"4MP"`

- **`sync_mode`** (`boolean`, _optional_):
  If true, returns the image directly in the response (increases latency).
  - Default: `false`



**Required Parameters Example**:

```json
{}
```

**Full Example**:

```json
{
  "prompt": "A hyper-detailed, ultra-fluffy owl sitting in the trees at night, looking directly at the camera with wide, adorable, expressive eyes. Its feathers are soft and voluminous, catching the cool moonlight with subtle silver highlights. The owl’s gaze is curious and full of charm, giving it a whimsical, storybook-like personality.",
  "seed": 5555,
  "steps_num": 50,
  "aspect_ratio": "1:1",
  "resolution": "1MP"
}
```


### Output Schema

The API returns the following output format:

- **`image`** (`Image`, _required_):
  Generated image.

- **`images`** (`list<object>`, _optional_):
  Generated images.
  - Default: `[]`
  - Array of object

- **`structured_prompt`** (`Structured Prompt`, _required_):
  Current prompt.



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
  },
  "images": []
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/bria/fibo/generate \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{}'
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
    "bria/fibo/generate",
    arguments={},
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

const result = await fal.subscribe("bria/fibo/generate", {
  input: {},
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

- [Model Playground](https://fal.ai/models/bria/fibo/generate)
- [API Documentation](https://fal.ai/models/bria/fibo/generate/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=bria/fibo/generate)

### fal.ai Platform

- [Platform Documentation](https://docs.fal.ai)
- [Python Client](https://docs.fal.ai/clients/python)
- [JavaScript Client](https://docs.fal.ai/clients/javascript)
