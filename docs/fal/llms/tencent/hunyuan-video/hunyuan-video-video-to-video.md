# Hunyuan Video (Video-to-Video)

> Hunyuan Video is an Open video generation model with high visual quality, motion diversity, text-video alignment, and generation stability. Use this endpoint to generate videos from videos.


## Overview

- **Endpoint**: `https://fal.run/fal-ai/hunyuan-video/video-to-video`
- **Model ID**: `fal-ai/hunyuan-video/video-to-video`
- **Category**: video-to-video
- **Kind**: inference
**Tags**: video to video, motion



## Pricing

- **Price**: $0 per compute seconds

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _required_):
  The prompt to generate the video from.
  - Examples: "A stylish woman walks down a Tokyo street filled with warm glowing neon and animated city signage. She wears a dark blue leather jacket, a long pink dress, and bright yellow boots, and carries a black purse."

- **`seed`** (`integer`, _optional_):
  The seed to use for generating the video.

- **`pro_mode`** (`boolean`, _optional_):
  By default, generations are done with 35 steps. Pro mode does 55 steps which results in higher quality videos but will take more time and cost 2x more billing units.
  - Default: `false`

- **`aspect_ratio`** (`AspectRatio(W:H)Enum`, _optional_):
  The aspect ratio of the video to generate. Default value: `"16:9"`
  - Default: `"16:9"`
  - Options: `"16:9"`, `"9:16"`

- **`resolution`** (`ResolutionEnum`, _optional_):
  The resolution of the video to generate. Default value: `"720p"`
  - Default: `"720p"`
  - Options: `"480p"`, `"580p"`, `"720p"`

- **`num_frames`** (`NumberofFramesEnum`, _optional_):
  The number of frames to generate. Default value: `"129"`
  - Default: `129`
  - Options: `"129"`, `"85"`

- **`enable_safety_checker`** (`boolean`, _optional_):
  If set to true, the safety checker will be enabled.
  - Default: `false`
  - Examples: true

- **`video_url`** (`string`, _required_):
  URL of the video input.
  - Examples: "https://storage.googleapis.com/falserverless/hunyuan_video/hunyuan_v2v_input.mp4"

- **`strength`** (`float`, _optional_):
  Strength for Video-to-Video Default value: `0.85`
  - Default: `0.85`
  - Range: `0.01` to `1`



**Required Parameters Example**:

```json
{
  "prompt": "A stylish woman walks down a Tokyo street filled with warm glowing neon and animated city signage. She wears a dark blue leather jacket, a long pink dress, and bright yellow boots, and carries a black purse.",
  "video_url": "https://storage.googleapis.com/falserverless/hunyuan_video/hunyuan_v2v_input.mp4"
}
```

**Full Example**:

```json
{
  "prompt": "A stylish woman walks down a Tokyo street filled with warm glowing neon and animated city signage. She wears a dark blue leather jacket, a long pink dress, and bright yellow boots, and carries a black purse.",
  "aspect_ratio": "16:9",
  "resolution": "720p",
  "num_frames": 129,
  "enable_safety_checker": true,
  "video_url": "https://storage.googleapis.com/falserverless/hunyuan_video/hunyuan_v2v_input.mp4",
  "strength": 0.85
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`File`, _required_)
  - Examples: {"url":"https://v3.fal.media/files/kangaroo/y5-1YTGpun17eSeggZMzX_video-1733468228.mp4"}

- **`seed`** (`integer`, _required_):
  The seed used for generating the video.



**Example Response**:

```json
{
  "video": {
    "url": "https://v3.fal.media/files/kangaroo/y5-1YTGpun17eSeggZMzX_video-1733468228.mp4"
  }
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/hunyuan-video/video-to-video \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "A stylish woman walks down a Tokyo street filled with warm glowing neon and animated city signage. She wears a dark blue leather jacket, a long pink dress, and bright yellow boots, and carries a black purse.",
     "video_url": "https://storage.googleapis.com/falserverless/hunyuan_video/hunyuan_v2v_input.mp4"
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
    "fal-ai/hunyuan-video/video-to-video",
    arguments={
        "prompt": "A stylish woman walks down a Tokyo street filled with warm glowing neon and animated city signage. She wears a dark blue leather jacket, a long pink dress, and bright yellow boots, and carries a black purse.",
        "video_url": "https://storage.googleapis.com/falserverless/hunyuan_video/hunyuan_v2v_input.mp4"
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

const result = await fal.subscribe("fal-ai/hunyuan-video/video-to-video", {
  input: {
    prompt: "A stylish woman walks down a Tokyo street filled with warm glowing neon and animated city signage. She wears a dark blue leather jacket, a long pink dress, and bright yellow boots, and carries a black purse.",
    video_url: "https://storage.googleapis.com/falserverless/hunyuan_video/hunyuan_v2v_input.mp4"
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

- [Model Playground](https://fal.ai/models/fal-ai/hunyuan-video/video-to-video)
- [API Documentation](https://fal.ai/models/fal-ai/hunyuan-video/video-to-video/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/hunyuan-video/video-to-video)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
