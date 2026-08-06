# Video

> High-fidelity keypoint-driven video object removal - minimal input, strong temporal consistency. Trained on licensed data for risk-free commercial video editing.


## Overview

- **Endpoint**: `https://fal.run/bria/video/erase/keypoints`
- **Model ID**: `bria/video/erase/keypoints`
- **Category**: video-to-video
- **Kind**: inference
**Tags**: bria, video, erase, keypoints



## Pricing

- **Price**: $0.14 per seconds

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`output_container_and_codec`** (`OutputContainerAndCodecEnum`, _optional_):
  Output container and codec. Options: mp4_h265, mp4_h264, webm_vp9, gif, mov_h264, mov_h265, mov_proresks, mkv_h264, mkv_h265, mkv_vp9, mkv_mpeg4. Default value: `"mp4_h264"`
  - Default: `"mp4_h264"`
  - Options: `"mp4_h265"`, `"mp4_h264"`, `"webm_vp9"`, `"gif"`, `"mov_h264"`, `"mov_h265"`, `"mov_proresks"`, `"mkv_h264"`, `"mkv_h265"`, `"mkv_vp9"`, `"mkv_mpeg4"`

- **`auto_trim`** (`boolean`, _optional_):
  auto trim the video, to working duration ( 5s ) Default value: `true`
  - Default: `true`

- **`preserve_audio`** (`boolean`, _optional_):
  If true, audio will be preserved in the output video. Default value: `true`
  - Default: `true`

- **`keypoints`** (`list<string>`, _required_):
  Input keypoints [x,y] to erase or keep from the video. Format like so: {'x':100, 'y':100, 'type':'positive/negative'}
  - Array of string
  - Examples: ["{'x': 765, 'y': 344, 'type': 'positive'}","{'x': 200, 'y': 200, 'type': 'negative'}"]

- **`video_url`** (`string`, _required_):
  Input video to erase object from. duration must be less than 5s.
  - Examples: "https://bria-test-images.s3.us-east-1.amazonaws.com/videos/eraser_mask/woman_right_side.mov"



**Required Parameters Example**:

```json
{
  "keypoints": [
    "{'x': 765, 'y': 344, 'type': 'positive'}",
    "{'x': 200, 'y': 200, 'type': 'negative'}"
  ],
  "video_url": "https://bria-test-images.s3.us-east-1.amazonaws.com/videos/eraser_mask/woman_right_side.mov"
}
```

**Full Example**:

```json
{
  "output_container_and_codec": "mp4_h264",
  "auto_trim": true,
  "preserve_audio": true,
  "keypoints": [
    "{'x': 765, 'y': 344, 'type': 'positive'}",
    "{'x': 200, 'y': 200, 'type': 'negative'}"
  ],
  "video_url": "https://bria-test-images.s3.us-east-1.amazonaws.com/videos/eraser_mask/woman_right_side.mov"
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`Video | File`, _required_):
  Final video.
  - One of: Video | File



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
  --url https://fal.run/bria/video/erase/keypoints \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "keypoints": [
       "{'x': 765, 'y': 344, 'type': 'positive'}",
       "{'x': 200, 'y': 200, 'type': 'negative'}"
     ],
     "video_url": "https://bria-test-images.s3.us-east-1.amazonaws.com/videos/eraser_mask/woman_right_side.mov"
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
    "bria/video/erase/keypoints",
    arguments={
        "keypoints": ["{'x': 765, 'y': 344, 'type': 'positive'}", "{'x': 200, 'y': 200, 'type': 'negative'}"],
        "video_url": "https://bria-test-images.s3.us-east-1.amazonaws.com/videos/eraser_mask/woman_right_side.mov"
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

const result = await fal.subscribe("bria/video/erase/keypoints", {
  input: {
    keypoints: ["{'x': 765, 'y': 344, 'type': 'positive'}", "{'x': 200, 'y': 200, 'type': 'negative'}"],
    video_url: "https://bria-test-images.s3.us-east-1.amazonaws.com/videos/eraser_mask/woman_right_side.mov"
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

- [Model Playground](https://fal.ai/models/bria/video/erase/keypoints)
- [API Documentation](https://fal.ai/models/bria/video/erase/keypoints/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=bria/video/erase/keypoints)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
