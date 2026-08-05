# Hunyuan Video Foley

> Use the capabilities of the hunyuan foley model to bring life to your videos by adding sound effect to them.


## Overview

- **Endpoint**: `https://fal.run/fal-ai/hunyuan-video-foley`
- **Model ID**: `fal-ai/hunyuan-video-foley`
- **Category**: video-to-video
- **Kind**: inference
**Tags**: video-to-video, add-sound



## Pricing

- **Price**: $0.1 per 10 seconds

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`video_url`** (`string`, _required_):
  The URL of the video to generate audio for.
  - Examples: "https://storage.googleapis.com/falserverless/model_tests/video_models/1_video.mp4"

- **`text_prompt`** (`string`, _required_):
  Text description of the desired audio (optional).
  - Examples: "A person walks on frozen ice", "The crackling of fire and whooshing of flames", "Gentle footsteps on wooden floor"

- **`negative_prompt`** (`string`, _optional_):
  Negative prompt to avoid certain audio characteristics. Default value: `"noisy, harsh"`
  - Default: `"noisy, harsh"`

- **`guidance_scale`** (`float`, _optional_):
  Guidance scale for audio generation. Default value: `4.5`
  - Default: `4.5`
  - Range: `1` to `10`

- **`num_inference_steps`** (`integer`, _optional_):
  Number of inference steps for generation. Default value: `50`
  - Default: `50`
  - Range: `10` to `100`

- **`seed`** (`integer`, _optional_):
  Random seed for reproducible generation.



**Required Parameters Example**:

```json
{
  "video_url": "https://storage.googleapis.com/falserverless/model_tests/video_models/1_video.mp4",
  "text_prompt": "A person walks on frozen ice"
}
```

**Full Example**:

```json
{
  "video_url": "https://storage.googleapis.com/falserverless/model_tests/video_models/1_video.mp4",
  "text_prompt": "A person walks on frozen ice",
  "negative_prompt": "noisy, harsh",
  "guidance_scale": 4.5,
  "num_inference_steps": 50
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`File`, _required_):
  List of generated video files with audio.



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
  --url https://fal.run/fal-ai/hunyuan-video-foley \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "video_url": "https://storage.googleapis.com/falserverless/model_tests/video_models/1_video.mp4",
     "text_prompt": "A person walks on frozen ice"
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
    "fal-ai/hunyuan-video-foley",
    arguments={
        "video_url": "https://storage.googleapis.com/falserverless/model_tests/video_models/1_video.mp4",
        "text_prompt": "A person walks on frozen ice"
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

const result = await fal.subscribe("fal-ai/hunyuan-video-foley", {
  input: {
    video_url: "https://storage.googleapis.com/falserverless/model_tests/video_models/1_video.mp4",
    text_prompt: "A person walks on frozen ice"
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

- [Model Playground](https://fal.ai/models/fal-ai/hunyuan-video-foley)
- [API Documentation](https://fal.ai/models/fal-ai/hunyuan-video-foley/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/hunyuan-video-foley)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
