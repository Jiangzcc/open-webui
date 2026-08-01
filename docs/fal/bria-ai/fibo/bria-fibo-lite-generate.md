# Fibo Lite

> Fast, low-latency text-to-image model with high-quality output and full JSON-structured controllability. Open-source, trained on licensed data, and optimized for production-scale generation.


## Overview

- **Endpoint**: `https://fal.run/bria/fibo-lite/generate`
- **Model ID**: `bria/fibo-lite/generate`
- **Category**: text-to-image
- **Kind**: inference
**Tags**: bria, fibo, lite



## Pricing

- **Price**: $0.036 per images

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _optional_):
  The prompt to generate.
  - Examples: "Oil painting of a fluffy, wide-eyed cat sitting upright, holding a small wooden sign reading \"Feed Me.\" Rich textures, dramatic brushstrokes, warm tones, and vintage charm."

- **`structured_prompt`** (`StructuredPrompt`, _optional_):
  The structured prompt to generate.

- **`image_url`** (`string`, _optional_):
  Input image URL

- **`seed`** (`integer`, _optional_):
  Seed for the random number generator. Default value: `7`
  - Default: `7`

- **`aspect_ratio`** (`AspectRatioEnum`, _optional_):
  Aspect ratio. Options: 1:1, 2:3, 3:2, 3:4, 4:3, 4:5, 5:4, 9:16, 16:9 Default value: `"1:1"`
  - Default: `"1:1"`
  - Options: `"1:1"`, `"2:3"`, `"3:2"`, `"3:4"`, `"4:3"`, `"4:5"`, `"5:4"`, `"9:16"`, `"16:9"`

- **`negative_prompt`** (`string`, _optional_):
  Negative prompt for image generation. Default value: `""`
  - Default: `""`

- **`steps_num`** (`integer`, _optional_):
  Number of inference steps. Default value: `8`
  - Default: `8`
  - Range: `4` to `30`

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
  "prompt": "Oil painting of a fluffy, wide-eyed cat sitting upright, holding a small wooden sign reading \"Feed Me.\" Rich textures, dramatic brushstrokes, warm tones, and vintage charm.",
  "seed": 7,
  "aspect_ratio": "1:1",
  "steps_num": 8
}
```


### Output Schema

The API returns the following output format:

- **`image`** (`Image`, _required_):
  Generated image.

- **`images`** (`list<object>`, _optional_):
  Generated images.
  - Array of object

- **`structured_prompt`** (`StructuredPrompt`, _required_):
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
  "structured_prompt": {
    "short_description": "",
    "objects": [
      {
        "description": "",
        "location": "",
        "relationship": ""
      }
    ],
    "background_setting": "",
    "lighting": {
      "conditions": "",
      "direction": ""
    },
    "aesthetics": {
      "composition": "",
      "color_scheme": "",
      "mood_atmosphere": "",
      "aesthetic_score": "",
      "preference_score": ""
    },
    "text_render": [
      {
        "text": "",
        "location": "",
        "size": "",
        "color": "",
        "font": ""
      }
    ],
    "context": "",
    "artistic_style": ""
  }
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/bria/fibo-lite/generate \
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
    "bria/fibo-lite/generate",
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

const result = await fal.subscribe("bria/fibo-lite/generate", {
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

- [Model Playground](https://fal.ai/models/bria/fibo-lite/generate)
- [API Documentation](https://fal.ai/models/bria/fibo-lite/generate/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=bria/fibo-lite/generate)

### fal.ai Platform

- [Platform Documentation](https://docs.fal.ai)
- [Python Client](https://docs.fal.ai/clients/python)
- [JavaScript Client](https://docs.fal.ai/clients/javascript)
