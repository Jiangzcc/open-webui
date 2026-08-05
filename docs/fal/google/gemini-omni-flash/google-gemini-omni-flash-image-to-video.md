# Gemini Omni Flash

> Animates a still image into video with audio. Extends a single frame into coherent motion, grounded in Gemini's physical understanding of how scenes and subjects behave.


## Overview

- **Endpoint**: `https://fal.run/google/gemini-omni-flash/image-to-video`
- **Model ID**: `google/gemini-omni-flash/image-to-video`
- **Category**: image-to-video
- **Kind**: inference
**Tags**: stylized, transform, lipsync



## Pricing

Billing is based on **total token consumption**. Input tokens (text/audio/video) cost **$1.875 per 1 million tokens**. Output tokens cost **$21.875 per 1 million tokens**. For 720p video this costs **approximately $0.13 per second of video**. 

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _required_):
  The text prompt describing how the image should be animated.
  - Examples: "The dog turns its head and wags its tail in warm sunlight."

- **`image_url`** (`string`, _required_):
  URL of the input image to animate.
  - Examples: "https://storage.googleapis.com/falserverless/example_inputs/dog.png"

- **`aspect_ratio`** (`AspectRatioEnum`, _optional_):
  The aspect ratio of the generated video. Default value: `"16:9"`
  - Default: `"16:9"`
  - Options: `"16:9"`, `"9:16"`

- **`duration`** (`integer`, _optional_):
  The duration of the generated video, in seconds. Default value: `8`
  - Default: `8`
  - Range: `3` to `10`



**Required Parameters Example**:

```json
{
  "prompt": "The dog turns its head and wags its tail in warm sunlight.",
  "image_url": "https://storage.googleapis.com/falserverless/example_inputs/dog.png"
}
```

**Full Example**:

```json
{
  "prompt": "The dog turns its head and wags its tail in warm sunlight.",
  "image_url": "https://storage.googleapis.com/falserverless/example_inputs/dog.png",
  "aspect_ratio": "16:9",
  "duration": 8
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`File`, _required_):
  The generated video.



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
  --url https://fal.run/google/gemini-omni-flash/image-to-video \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "The dog turns its head and wags its tail in warm sunlight.",
     "image_url": "https://storage.googleapis.com/falserverless/example_inputs/dog.png"
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
    "google/gemini-omni-flash/image-to-video",
    arguments={
        "prompt": "The dog turns its head and wags its tail in warm sunlight.",
        "image_url": "https://storage.googleapis.com/falserverless/example_inputs/dog.png"
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

const result = await fal.subscribe("google/gemini-omni-flash/image-to-video", {
  input: {
    prompt: "The dog turns its head and wags its tail in warm sunlight.",
    image_url: "https://storage.googleapis.com/falserverless/example_inputs/dog.png"
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

- [Model Playground](https://fal.ai/models/google/gemini-omni-flash/image-to-video)
- [API Documentation](https://fal.ai/models/google/gemini-omni-flash/image-to-video/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=google/gemini-omni-flash/image-to-video)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
