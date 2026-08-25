# DWPose Pose Prediction

> Predict poses from videos.


## Overview

- **Endpoint**: `https://fal.run/fal-ai/dwpose/video`
- **Model ID**: `fal-ai/dwpose/video`
- **Category**: video-to-video
- **Kind**: inference
**Tags**: pose, utility



## Pricing

Your request will cost $0.0006 per compute second.

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`video_url`** (`string`, _required_):
  URL of video to be used for pose estimation
  - Examples: "https://storage.googleapis.com/falserverless/gallery/Ben2/100063-video-2160.mp4"

- **`draw_mode`** (`DrawModeEnum`, _optional_):
  Mode of drawing the pose on the video. Options are: 'full-pose', 'body-pose', 'face-pose', 'hand-pose', 'face-hand-mask', 'face-mask', 'hand-mask'. Default value: `"body-pose"`
  - Default: `"body-pose"`
  - Options: `"full-pose"`, `"body-pose"`, `"face-pose"`, `"hand-pose"`, `"face-hand-mask"`, `"face-mask"`, `"hand-mask"`
  - Examples: "body-pose"



**Required Parameters Example**:

```json
{
  "video_url": "https://storage.googleapis.com/falserverless/gallery/Ben2/100063-video-2160.mp4"
}
```

**Full Example**:

```json
{
  "video_url": "https://storage.googleapis.com/falserverless/gallery/Ben2/100063-video-2160.mp4",
  "draw_mode": "body-pose"
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`File`, _required_):
  The output video with pose estimation.
  - Examples: {"content_type":"video/mp4","url":"https://storage.googleapis.com/falserverless/example_outputs/dwpose-video-output.mp4"}



**Example Response**:

```json
{
  "video": {
    "content_type": "video/mp4",
    "url": "https://storage.googleapis.com/falserverless/example_outputs/dwpose-video-output.mp4"
  }
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/dwpose/video \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "video_url": "https://storage.googleapis.com/falserverless/gallery/Ben2/100063-video-2160.mp4"
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
    "fal-ai/dwpose/video",
    arguments={
        "video_url": "https://storage.googleapis.com/falserverless/gallery/Ben2/100063-video-2160.mp4"
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

const result = await fal.subscribe("fal-ai/dwpose/video", {
  input: {
    video_url: "https://storage.googleapis.com/falserverless/gallery/Ben2/100063-video-2160.mp4"
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

- [Model Playground](https://fal.ai/models/fal-ai/dwpose/video)
- [API Documentation](https://fal.ai/models/fal-ai/dwpose/video/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/dwpose/video)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
