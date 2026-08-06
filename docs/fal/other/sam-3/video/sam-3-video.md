# Sam 3

> SAM 3 is a unified foundation model for promptable segmentation in images and videos. It can detect, segment, and track objects using text or visual prompts such as points, boxes, and masks. 


## Overview

- **Endpoint**: `https://fal.run/fal-ai/sam-3/video`
- **Model ID**: `fal-ai/sam-3/video`
- **Category**: video-to-video
- **Kind**: inference
**Tags**: segmentation, mask, real-time



## Pricing

Your request will cost $0.005 per 16 frames of video input.

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`video_url`** (`string`, _required_):
  The URL of the video to be segmented.

- **`prompt`** (`string`, _optional_):
  Text prompt for segmentation. Use commas to track multiple objects (e.g., 'person, cloth'). Default value: `""`
  - Default: `""`
  - Examples: "person", "person, cloth"

- **`point_prompts`** (`list<PointPromptBase>`, _optional_):
  List of point prompts
  - Default: `[]`
  - Array of PointPromptBase

- **`box_prompts`** (`list<BoxPromptBase>`, _optional_):
  List of box prompt coordinates (x_min, y_min, x_max, y_max).
  - Default: `[]`
  - Array of BoxPromptBase

- **`apply_mask`** (`boolean`, _optional_):
  Apply the mask on the video. Default value: `true`
  - Default: `true`

- **`video_output_type`** (`VideoOutputTypeEnum`, _optional_):
  The output type of the generated video. Default value: `"X264 (.mp4)"`
  - Default: `"X264 (.mp4)"`
  - Options: `"X264 (.mp4)"`, `"VP9 (.webm)"`

- **`detection_threshold`** (`float`, _optional_):
  Detection confidence threshold (0.0-1.0). Lower = more detections but less precise. Default value: `0.5`
  - Default: `0.5`
  - Range: `0.1` to `1`



**Required Parameters Example**:

```json
{
  "video_url": ""
}
```

**Full Example**:

```json
{
  "video_url": "",
  "prompt": "person",
  "point_prompts": [],
  "box_prompts": [],
  "apply_mask": true,
  "video_output_type": "X264 (.mp4)",
  "detection_threshold": 0.5
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`File`, _required_):
  The segmented video.
  - Examples: "https://fal.media/files/monkey/5BLHmbX3qxu5cD5gQzTqw_output.mp4"

- **`boundingbox_frames_zip`** (`File`, _optional_):
  Zip file containing per-frame bounding box overlays.



**Example Response**:

```json
{
  "video": "https://fal.media/files/monkey/5BLHmbX3qxu5cD5gQzTqw_output.mp4"
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/sam-3/video \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "video_url": ""
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
    "fal-ai/sam-3/video",
    arguments={
        "video_url": ""
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

const result = await fal.subscribe("fal-ai/sam-3/video", {
  input: {
    video_url: ""
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

- [Model Playground](https://fal.ai/models/fal-ai/sam-3/video)
- [API Documentation](https://fal.ai/models/fal-ai/sam-3/video/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/sam-3/video)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
