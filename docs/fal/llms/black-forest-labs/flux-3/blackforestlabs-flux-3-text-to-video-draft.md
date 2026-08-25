# Flux 3 Text To Video Draft

> FLUX.3 is Black Forest Labs' frontier audio/video model. Generate fast, low-cost draft previews from a text prompt, with a reusable draft cache for full-quality enhancement.



## Overview

- **Endpoint**: `https://fal.run/blackforestlabs/flux-3/text-to-video/draft`
- **Model ID**: `blackforestlabs/flux-3/text-to-video/draft`
- **Category**: text-to-video
- **Kind**: inference
**Tags**: stylized, transform, lipsync



## Pricing

Your request will be charged at **0.06** $ per second of generated draft video (720p).

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _required_):
  The text prompt describing the draft video.
  - Examples: "A red panda walks along a mossy log in a sunlit forest, one continuous unbroken shot."

- **`aspect_ratio`** (`AspectRatioEnum`, _optional_):
  Aspect ratio of the generated draft. `auto` lets the model choose. Default value: `"auto"`
  - Default: `"auto"`
  - Options: `"auto"`, `"21:9"`, `"2:1"`, `"16:9"`, `"4:3"`, `"1:1"`, `"3:4"`, `"9:16"`

- **`duration`** (`DurationEnum`, _optional_):
  Draft duration in whole seconds from 5 through 20, or `auto`. Default value: `"auto"`
  - Default: `"auto"`
  - Options: `"auto"`, `5`, `6`, `7`, `8`, `9`, `10`, `11`, `12`, `13`, `14`, `15`, `16`, `17`, `18`, `19`, `20`

- **`generate_audio`** (`boolean`, _optional_):
  Whether to generate audio for the draft video. Default value: `true`
  - Default: `true`

- **`safety_tolerance`** (`integer`, _optional_):
  The safety tolerance level for the generated video. 0 is the strictest and 4 is the most permissive. Default value: `2`
  - Default: `2`
  - Range: `0` to `4`



**Required Parameters Example**:

```json
{
  "prompt": "A red panda walks along a mossy log in a sunlit forest, one continuous unbroken shot."
}
```

**Full Example**:

```json
{
  "prompt": "A red panda walks along a mossy log in a sunlit forest, one continuous unbroken shot.",
  "aspect_ratio": "auto",
  "duration": "auto",
  "generate_audio": true,
  "safety_tolerance": 2
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`File`, _required_):
  The draft video.

- **`draft_cache`** (`File`, _required_):
  Durable encrypted cache bundle; pass it to `draft-enhance` for a full-quality render.



**Example Response**:

```json
{
  "video": {
    "url": "",
    "content_type": "image/png",
    "file_name": "z9RV14K95DvU.png",
    "file_size": 4404019
  },
  "draft_cache": {
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
  --url https://fal.run/blackforestlabs/flux-3/text-to-video/draft \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "A red panda walks along a mossy log in a sunlit forest, one continuous unbroken shot."
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
    "blackforestlabs/flux-3/text-to-video/draft",
    arguments={
        "prompt": "A red panda walks along a mossy log in a sunlit forest, one continuous unbroken shot."
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

const result = await fal.subscribe("blackforestlabs/flux-3/text-to-video/draft", {
  input: {
    prompt: "A red panda walks along a mossy log in a sunlit forest, one continuous unbroken shot."
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

- [Model Playground](https://fal.ai/models/blackforestlabs/flux-3/text-to-video/draft)
- [API Documentation](https://fal.ai/models/blackforestlabs/flux-3/text-to-video/draft/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=blackforestlabs/flux-3/text-to-video/draft)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
