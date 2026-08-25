# DeepSeek Janus-Pro

> DeepSeek Janus-Pro is a novel text-to-image model that unifies multimodal understanding and generation through an autoregressive framework


## Overview

- **Endpoint**: `https://fal.run/fal-ai/janus`
- **Model ID**: `fal-ai/janus`
- **Category**: text-to-image
- **Kind**: inference
**Tags**: stylized



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
  - Examples: "beautiful girl, inside a house"

- **`image_size`** (`ImageSize | Enum`, _optional_):
  The size of the generated image. Default value: `square`
  - Default: `"square"`
  - One of: ImageSize | Enum

- **`temperature`** (`float`, _optional_):
  Controls randomness in the generation. Higher values make output more random. Default value: `1`
  - Default: `1`
  - Range: `0.1` to `2`

- **`cfg_weight`** (`float`, _optional_):
  Classifier Free Guidance scale - how closely to follow the prompt. Default value: `5`
  - Default: `5`
  - Range: `1` to `20`

- **`num_images`** (`integer`, _optional_):
  Number of images to generate in parallel. Default value: `1`
  - Default: `1`
  - Range: `1` to `16`

- **`seed`** (`integer`, _optional_):
  Random seed for reproducible generation.

- **`enable_safety_checker`** (`boolean`, _optional_):
  If set to true, the safety checker will be enabled. Default value: `true`
  - Default: `true`

- **`output_format`** (`OutputFormatEnum`, _optional_):
  The format of the generated image. Default value: `"png"`
  - Default: `"png"`
  - Options: `"jpeg"`, `"png"`



**Required Parameters Example**:

```json
{
  "prompt": "beautiful girl, inside a house"
}
```

**Full Example**:

```json
{
  "prompt": "beautiful girl, inside a house",
  "image_size": "square",
  "temperature": 1,
  "cfg_weight": 5,
  "num_images": 1,
  "enable_safety_checker": true,
  "output_format": "png"
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
  --url https://fal.run/fal-ai/janus \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "beautiful girl, inside a house"
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
    "fal-ai/janus",
    arguments={
        "prompt": "beautiful girl, inside a house"
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

const result = await fal.subscribe("fal-ai/janus", {
  input: {
    prompt: "beautiful girl, inside a house"
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

- [Model Playground](https://fal.ai/models/fal-ai/janus)
- [API Documentation](https://fal.ai/models/fal-ai/janus/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/janus)

### fal.ai Platform

- [Platform Documentation](https://docs.fal.ai)
- [Python Client](https://docs.fal.ai/clients/python)
- [JavaScript Client](https://docs.fal.ai/clients/javascript)
