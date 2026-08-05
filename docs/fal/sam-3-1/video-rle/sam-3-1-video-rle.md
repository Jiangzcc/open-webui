# Sam 3 1

> SAM 3.1 builds comes with Object Multiplex, a shared-memory approach for joint multi-object tracking that delivers faster speeds with larger number of objects tracked.


## Overview

- **Endpoint**: `https://fal.run/fal-ai/sam-3-1/video-rle`
- **Model ID**: `fal-ai/sam-3-1/video-rle`
- **Category**: video-to-video
- **Kind**: inference
**Tags**: segmentation, mask, real-time



## Pricing

Your request will cost $0.01 per 16 frames of video input.

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`video_url`** (`string`, _required_):
  The URL of the video to be segmented.
  - Examples: "https://v3b.fal.media/files/b/elephant/NQdDxB0Ddfo82SPLbhYDp_bedroom.mp4"

- **`mask_url`** (`string`, _optional_):
  The URL of the mask to be applied initially.

- **`prompt`** (`string`, _optional_):
  Text prompt for segmentation. Use commas to track multiple objects (e.g., 'person, cloth'). Default value: `""`
  - Default: `""`
  - Examples: "person", "person, cloth"

- **`point_prompts`** (`list<PointPrompt>`, _optional_):
  List of point prompts with frame indices.
  - Default: `[]`
  - Array of PointPrompt

- **`box_prompts`** (`list<BoxPrompt>`, _optional_):
  List of box prompts with optional frame_index.
  - Default: `[]`
  - Array of BoxPrompt

- **`apply_mask`** (`boolean`, _optional_):
  Apply the mask on the video.
  - Default: `false`

- **`boundingbox_zip`** (`boolean`, _optional_):
  Return per-frame bounding box overlays as a zip archive.
  - Default: `false`

- **`detection_threshold`** (`float`, _optional_):
  Detection confidence threshold (0.0-1.0). Lower = more detections but less precise. Defaults: 0.5 for existing, 0.7 for new objects. Try 0.2-0.3 if text prompts fail. Default value: `0.5`
  - Default: `0.5`
  - Range: `0.01` to `1`

- **`frame_index`** (`integer`, _optional_):
  Frame index used for initial interaction when mask_url is provided.
  - Default: `0`

- **`max_num_objects`** (`integer`, _optional_):
  Maximum number of objects to track in the video. Default value: `16`
  - Default: `16`
  - Range: `1` to `128`



**Required Parameters Example**:

```json
{
  "video_url": "https://v3b.fal.media/files/b/elephant/NQdDxB0Ddfo82SPLbhYDp_bedroom.mp4"
}
```

**Full Example**:

```json
{
  "video_url": "https://v3b.fal.media/files/b/elephant/NQdDxB0Ddfo82SPLbhYDp_bedroom.mp4",
  "prompt": "person",
  "point_prompts": [],
  "box_prompts": [],
  "detection_threshold": 0.5,
  "max_num_objects": 16
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`File`, _required_):
  The segmented video.
  - Examples: "https://fal.media/files/lion/gr-RSvy2e7_AWbjxAq4mJ_output.mp4"

- **`boundingbox_frames_zip`** (`File`, _optional_):
  Zip file containing per-frame bounding box overlays.



**Example Response**:

```json
{
  "video": "https://fal.media/files/lion/gr-RSvy2e7_AWbjxAq4mJ_output.mp4"
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/sam-3-1/video-rle \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "video_url": "https://v3b.fal.media/files/b/elephant/NQdDxB0Ddfo82SPLbhYDp_bedroom.mp4"
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
    "fal-ai/sam-3-1/video-rle",
    arguments={
        "video_url": "https://v3b.fal.media/files/b/elephant/NQdDxB0Ddfo82SPLbhYDp_bedroom.mp4"
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

const result = await fal.subscribe("fal-ai/sam-3-1/video-rle", {
  input: {
    video_url: "https://v3b.fal.media/files/b/elephant/NQdDxB0Ddfo82SPLbhYDp_bedroom.mp4"
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

- [Model Playground](https://fal.ai/models/fal-ai/sam-3-1/video-rle)
- [API Documentation](https://fal.ai/models/fal-ai/sam-3-1/video-rle/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/sam-3-1/video-rle)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
