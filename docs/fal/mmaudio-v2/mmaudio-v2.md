# MMAudio V2

> MMAudio generates synchronized audio given video and/or text inputs. It can be combined with video models to get videos with audio.


## Overview

- **Endpoint**: `https://fal.run/fal-ai/mmaudio-v2`
- **Model ID**: `fal-ai/mmaudio-v2`
- **Category**: video-to-video
- **Kind**: inference
**Tags**: ai video, fast



## Pricing

- **Price**: $0.001 per seconds

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`video_url`** (`string`, _required_):
  The URL of the video to generate the audio for.
  - Examples: "https://storage.googleapis.com/falserverless/model_tests/video_models/mmaudio_input.mp4"

- **`prompt`** (`string`, _required_):
  The prompt to generate the audio for.
  - Examples: "Indian holy music"

- **`negative_prompt`** (`string`, _optional_):
  The negative prompt to generate the audio for. Default value: `""`
  - Default: `""`

- **`seed`** (`integer`, _optional_):
  The seed for the random number generator
  - Range: `0` to `65535`

- **`num_steps`** (`integer`, _optional_):
  The number of steps to generate the audio for. Default value: `25`
  - Default: `25`
  - Range: `4` to `50`

- **`duration`** (`float`, _optional_):
  The duration of the audio to generate. Default value: `8`
  - Default: `8`
  - Range: `1` to `30`

- **`cfg_strength`** (`float`, _optional_):
  The strength of Classifier Free Guidance. Default value: `4.5`
  - Default: `4.5`
  - Range: `0` to `20`

- **`mask_away_clip`** (`boolean`, _optional_):
  Whether to mask away the clip.
  - Default: `false`



**Required Parameters Example**:

```json
{
  "video_url": "https://storage.googleapis.com/falserverless/model_tests/video_models/mmaudio_input.mp4",
  "prompt": "Indian holy music"
}
```

**Full Example**:

```json
{
  "video_url": "https://storage.googleapis.com/falserverless/model_tests/video_models/mmaudio_input.mp4",
  "prompt": "Indian holy music",
  "num_steps": 25,
  "duration": 8,
  "cfg_strength": 4.5
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`File`, _required_):
  The generated video with the lip sync.
  - Examples: {"content_type":"application/octet-stream","file_size":1001342,"url":"https://storage.googleapis.com/falserverless/model_tests/video_models/mmaudio_output.mp4","file_name":"mmaudio_input.mp4"}



**Example Response**:

```json
{
  "video": {
    "content_type": "application/octet-stream",
    "file_size": 1001342,
    "url": "https://storage.googleapis.com/falserverless/model_tests/video_models/mmaudio_output.mp4",
    "file_name": "mmaudio_input.mp4"
  }
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/mmaudio-v2 \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "video_url": "https://storage.googleapis.com/falserverless/model_tests/video_models/mmaudio_input.mp4",
     "prompt": "Indian holy music"
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
    "fal-ai/mmaudio-v2",
    arguments={
        "video_url": "https://storage.googleapis.com/falserverless/model_tests/video_models/mmaudio_input.mp4",
        "prompt": "Indian holy music"
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

const result = await fal.subscribe("fal-ai/mmaudio-v2", {
  input: {
    video_url: "https://storage.googleapis.com/falserverless/model_tests/video_models/mmaudio_input.mp4",
    prompt: "Indian holy music"
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

- [Model Playground](https://fal.ai/models/fal-ai/mmaudio-v2)
- [API Documentation](https://fal.ai/models/fal-ai/mmaudio-v2/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/mmaudio-v2)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
