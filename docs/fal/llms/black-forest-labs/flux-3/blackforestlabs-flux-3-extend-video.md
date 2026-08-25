# Flux 3 Extend Video

> FLUX.3 is Black Forest Labs' frontier video model. This endpoint continues an existing clip beyond its final frame, generating additional footage that stays consistent with the original motion and scene.


## Overview

- **Endpoint**: `https://fal.run/blackforestlabs/flux-3/extend-video`
- **Model ID**: `blackforestlabs/flux-3/extend-video`
- **Category**: video-to-video
- **Kind**: inference
**Tags**: stylized, transform, lipsync



## Pricing

Your request will be charged at **0.41** $ per second of generated video at 720p, and **0.53** $ per second at 1080p.

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _required_):
  The text prompt describing how the video continues from the source clip's final frames.
  - Examples: "The camera keeps tracking as the subject turns and smiles."

- **`aspect_ratio`** (`AspectRatioEnum`, _optional_):
  Aspect ratio of the generated video. `auto` lets the model choose. Default value: `"auto"`
  - Default: `"auto"`
  - Options: `"auto"`, `"21:9"`, `"2:1"`, `"16:9"`, `"4:3"`, `"1:1"`, `"3:4"`, `"9:16"`

- **`resolution`** (`ResolutionEnum`, _optional_):
  Resolution of the generated video. Default value: `"720p"`
  - Default: `"720p"`
  - Options: `"720p"`, `"1080p"`

- **`duration`** (`DurationEnum`, _optional_):
  Duration of the generated video in seconds. `auto` lets the model choose. Default value: `"auto"`
  - Default: `"auto"`
  - Options: `"auto"`, `5`, `6`, `7`, `8`, `9`, `10`, `11`, `12`, `13`, `14`, `15`, `16`, `17`, `18`, `19`, `20`

- **`generate_audio`** (`boolean`, _optional_):
  Whether to generate audio for the video. Default value: `true`
  - Default: `true`

- **`safety_tolerance`** (`integer`, _optional_):
  The safety tolerance level for the generated video. 0 is the strictest and 4 is the most permissive. Default value: `2`
  - Default: `2`
  - Range: `0` to `4`

- **`video_url`** (`string`, _required_):
  URL of the input video. MP4, under 50 MB and under 15 seconds.
  - Examples: "https://storage.googleapis.com/falserverless/example_inputs/flux-3-red-panda.mp4"



**Required Parameters Example**:

```json
{
  "prompt": "The camera keeps tracking as the subject turns and smiles.",
  "video_url": "https://storage.googleapis.com/falserverless/example_inputs/flux-3-red-panda.mp4"
}
```

**Full Example**:

```json
{
  "prompt": "The camera keeps tracking as the subject turns and smiles.",
  "aspect_ratio": "auto",
  "resolution": "720p",
  "duration": "auto",
  "generate_audio": true,
  "safety_tolerance": 2,
  "video_url": "https://storage.googleapis.com/falserverless/example_inputs/flux-3-red-panda.mp4"
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`File`, _required_):
  The generated video.
  - Examples: {"url":"https://storage.googleapis.com/falserverless/example_outputs/veo3-i2v-output.mp4"}

- **`seed`** (`integer`, _required_):
  The seed used for the generation.



**Example Response**:

```json
{
  "video": {
    "url": "https://storage.googleapis.com/falserverless/example_outputs/veo3-i2v-output.mp4"
  }
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/blackforestlabs/flux-3/extend-video \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "The camera keeps tracking as the subject turns and smiles.",
     "video_url": "https://storage.googleapis.com/falserverless/example_inputs/flux-3-red-panda.mp4"
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
    "blackforestlabs/flux-3/extend-video",
    arguments={
        "prompt": "The camera keeps tracking as the subject turns and smiles.",
        "video_url": "https://storage.googleapis.com/falserverless/example_inputs/flux-3-red-panda.mp4"
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

const result = await fal.subscribe("blackforestlabs/flux-3/extend-video", {
  input: {
    prompt: "The camera keeps tracking as the subject turns and smiles.",
    video_url: "https://storage.googleapis.com/falserverless/example_inputs/flux-3-red-panda.mp4"
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

- [Model Playground](https://fal.ai/models/blackforestlabs/flux-3/extend-video)
- [API Documentation](https://fal.ai/models/blackforestlabs/flux-3/extend-video/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=blackforestlabs/flux-3/extend-video)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
