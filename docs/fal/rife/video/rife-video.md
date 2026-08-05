# RIFE

> Interpolate videos with RIFE - Real-Time Intermediate Flow Estimation


## Overview

- **Endpoint**: `https://fal.run/fal-ai/rife/video`
- **Model ID**: `fal-ai/rife/video`
- **Category**: video-to-video
- **Kind**: inference
**Tags**: interpolation



## Pricing

Your request will cost **$0.0013** per compute second.

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`video_url`** (`string`, _required_):
  The URL of the video to use for interpolation.
  - Examples: "https://storage.googleapis.com/falserverless/example_inputs/interpolation-video-input.mp4"

- **`num_frames`** (`integer`, _optional_):
  The number of frames to generate between the input video frames. Default value: `1`
  - Default: `1`
  - Range: `1` to `4`

- **`use_scene_detection`** (`boolean`, _optional_):
  If True, the input video will be split into scenes before interpolation. This removes smear frames between scenes, but can result in false positives if the scene detection is not accurate. If False, the entire video will be treated as a single scene.
  - Default: `false`

- **`use_calculated_fps`** (`boolean`, _optional_):
  If True, the function will use the calculated FPS of the input video multiplied by the number of frames to determine the output FPS. If False, the passed FPS will be used. Default value: `true`
  - Default: `true`

- **`fps`** (`integer`, _optional_):
  Frames per second for the output video. Only applicable if use_calculated_fps is False. Default value: `8`
  - Default: `8`
  - Range: `1` to `60`

- **`loop`** (`boolean`, _optional_):
  If True, the final frame will be looped back to the first frame to create a seamless loop. If False, the final frame will not loop back.
  - Default: `false`



**Required Parameters Example**:

```json
{
  "video_url": "https://storage.googleapis.com/falserverless/example_inputs/interpolation-video-input.mp4"
}
```

**Full Example**:

```json
{
  "video_url": "https://storage.googleapis.com/falserverless/example_inputs/interpolation-video-input.mp4",
  "num_frames": 1,
  "use_calculated_fps": true,
  "fps": 8
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`File`, _required_):
  The generated video file with interpolated frames.
  - Examples: {"url":"https://storage.googleapis.com/falserverless/example_outputs/rife-video-output.mp4"}



**Example Response**:

```json
{
  "video": {
    "url": "https://storage.googleapis.com/falserverless/example_outputs/rife-video-output.mp4"
  }
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/rife/video \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "video_url": "https://storage.googleapis.com/falserverless/example_inputs/interpolation-video-input.mp4"
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
    "fal-ai/rife/video",
    arguments={
        "video_url": "https://storage.googleapis.com/falserverless/example_inputs/interpolation-video-input.mp4"
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

const result = await fal.subscribe("fal-ai/rife/video", {
  input: {
    video_url: "https://storage.googleapis.com/falserverless/example_inputs/interpolation-video-input.mp4"
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

- [Model Playground](https://fal.ai/models/fal-ai/rife/video)
- [API Documentation](https://fal.ai/models/fal-ai/rife/video/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/rife/video)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
