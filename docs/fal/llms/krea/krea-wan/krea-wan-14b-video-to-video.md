# Krea Wan 14B

> Superfast video model based on Wan 2.1 14b by Krea, excelling at real-time video-editing.


## Overview

- **Endpoint**: `https://fal.run/fal-ai/krea-wan-14b/video-to-video`
- **Model ID**: `fal-ai/krea-wan-14b/video-to-video`
- **Category**: video-to-video
- **Kind**: inference


## Pricing

Generation will cost **$0.025** per output video second. Video seconds are calculated at 16 frames per second.

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _required_):
  Prompt for the video-to-video generation.
  - Examples: "A powerful, matte black jeep, its robust frame contrasting with the lush green surroundings, navigates a winding jungle road, kicking up small clouds of dust and loose earth from its tires."

- **`strength`** (`float`, _optional_):
  Denoising strength for the video-to-video generation. 0.0 preserves the original, 1.0 completely remakes the video. Default value: `0.85`
  - Default: `0.85`
  - Range: `0.01` to `1`

- **`enable_prompt_expansion`** (`boolean`, _optional_):
  Whether to enable prompt expansion. This will use a large language model to expand the prompt with additional details while maintaining the original meaning.
  - Default: `false`
  - Examples: true

- **`video_url`** (`string`, _required_):
  URL of the input video. Currently, only outputs of 16:9 aspect ratio and 480p resolution are supported. Video duration should be less than 1000 frames at 16fps, and output frames will be 6 plus a multiple of 12, for example 18, 30, 42, etc.
  - Examples: "https://storage.googleapis.com/falserverless/example_inputs/krea_wan_14b_v2v_input.mp4"

- **`seed`** (`integer`, _optional_):
  Seed for the video-to-video generation.



**Required Parameters Example**:

```json
{
  "prompt": "A powerful, matte black jeep, its robust frame contrasting with the lush green surroundings, navigates a winding jungle road, kicking up small clouds of dust and loose earth from its tires.",
  "video_url": "https://storage.googleapis.com/falserverless/example_inputs/krea_wan_14b_v2v_input.mp4"
}
```

**Full Example**:

```json
{
  "prompt": "A powerful, matte black jeep, its robust frame contrasting with the lush green surroundings, navigates a winding jungle road, kicking up small clouds of dust and loose earth from its tires.",
  "strength": 0.85,
  "enable_prompt_expansion": true,
  "video_url": "https://storage.googleapis.com/falserverless/example_inputs/krea_wan_14b_v2v_input.mp4"
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`File`, _required_):
  The generated video file.
  - Examples: {"url":"https://storage.googleapis.com/falserverless/example_outputs/krea_wan_14b_v2v_output.mp4"}



**Example Response**:

```json
{
  "video": {
    "url": "https://storage.googleapis.com/falserverless/example_outputs/krea_wan_14b_v2v_output.mp4"
  }
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/krea-wan-14b/video-to-video \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "A powerful, matte black jeep, its robust frame contrasting with the lush green surroundings, navigates a winding jungle road, kicking up small clouds of dust and loose earth from its tires.",
     "video_url": "https://storage.googleapis.com/falserverless/example_inputs/krea_wan_14b_v2v_input.mp4"
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
    "fal-ai/krea-wan-14b/video-to-video",
    arguments={
        "prompt": "A powerful, matte black jeep, its robust frame contrasting with the lush green surroundings, navigates a winding jungle road, kicking up small clouds of dust and loose earth from its tires.",
        "video_url": "https://storage.googleapis.com/falserverless/example_inputs/krea_wan_14b_v2v_input.mp4"
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

const result = await fal.subscribe("fal-ai/krea-wan-14b/video-to-video", {
  input: {
    prompt: "A powerful, matte black jeep, its robust frame contrasting with the lush green surroundings, navigates a winding jungle road, kicking up small clouds of dust and loose earth from its tires.",
    video_url: "https://storage.googleapis.com/falserverless/example_inputs/krea_wan_14b_v2v_input.mp4"
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

- [Model Playground](https://fal.ai/models/fal-ai/krea-wan-14b/video-to-video)
- [API Documentation](https://fal.ai/models/fal-ai/krea-wan-14b/video-to-video/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/krea-wan-14b/video-to-video)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
