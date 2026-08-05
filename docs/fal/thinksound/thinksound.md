# ThinkSound

> Generate realistic audio for a video with an optional text prompt and combine


## Overview

- **Endpoint**: `https://fal.run/fal-ai/thinksound`
- **Model ID**: `fal-ai/thinksound`
- **Category**: video-to-video
- **Kind**: inference
**Tags**: audio-generation, video-to-audio



## Pricing

Your request will cost **$0.001** per compute second.

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`video_url`** (`string`, _required_):
  The URL of the video to generate the audio for.
  - Examples: "https://storage.googleapis.com/falserverless/example_inputs/thinksound-input.mp4"

- **`prompt`** (`string`, _optional_):
  A prompt to guide the audio generation. If not provided, it will be extracted from the video. Default value: `""`
  - Default: `""`

- **`seed`** (`integer`, _optional_):
  The seed for the random number generator

- **`num_inference_steps`** (`integer`, _optional_):
  The number of inference steps for audio generation. Default value: `24`
  - Default: `24`
  - Range: `2` to `100`
  - Examples: 24

- **`cfg_scale`** (`float`, _optional_):
  The classifier-free guidance scale for audio generation. Default value: `5`
  - Default: `5`
  - Range: `1` to `20`
  - Examples: 5



**Required Parameters Example**:

```json
{
  "video_url": "https://storage.googleapis.com/falserverless/example_inputs/thinksound-input.mp4"
}
```

**Full Example**:

```json
{
  "video_url": "https://storage.googleapis.com/falserverless/example_inputs/thinksound-input.mp4",
  "num_inference_steps": 24,
  "cfg_scale": 5
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`File`, _required_):
  The generated video with audio.
  - Examples: {"url":"https://storage.googleapis.com/falserverless/example_outputs/thinksound-output.mp4"}

- **`prompt`** (`string`, _required_):
  The prompt used to generate the audio.
  - Examples: "An acoustic guitar being played indoors."



**Example Response**:

```json
{
  "video": {
    "url": "https://storage.googleapis.com/falserverless/example_outputs/thinksound-output.mp4"
  },
  "prompt": "An acoustic guitar being played indoors."
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/thinksound \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "video_url": "https://storage.googleapis.com/falserverless/example_inputs/thinksound-input.mp4"
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
    "fal-ai/thinksound",
    arguments={
        "video_url": "https://storage.googleapis.com/falserverless/example_inputs/thinksound-input.mp4"
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

const result = await fal.subscribe("fal-ai/thinksound", {
  input: {
    video_url: "https://storage.googleapis.com/falserverless/example_inputs/thinksound-input.mp4"
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

- [Model Playground](https://fal.ai/models/fal-ai/thinksound)
- [API Documentation](https://fal.ai/models/fal-ai/thinksound/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/thinksound)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
