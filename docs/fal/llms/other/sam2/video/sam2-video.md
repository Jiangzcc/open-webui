# Segment Anything Model 2

> SAM 2 is a model for segmenting images and videos in real-time.


## Overview

- **Endpoint**: `https://fal.run/fal-ai/sam2/video`
- **Model ID**: `fal-ai/sam2/video`
- **Category**: video-to-video
- **Kind**: inference
**Tags**: segmentation, mask, real-time



## Pricing

- **Price**: $0 per compute seconds

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`video_url`** (`string`, _required_):
  The URL of the video to be segmented.
  - Examples: "https://drive.google.com/uc?id=1iOFYbNITYwrebBBp9kaEGhBndFSRLz8k"

- **`mask_url`** (`string`, _optional_):
  The URL of the mask to be applied initially.

- **`prompts`** (`list<PointPrompt>`, _optional_):
  List of prompts to segment the video
  - Default: `[]`
  - Array of PointPrompt
  - Examples: [{"frame_index":0,"y":350,"x":210,"label":1},{"frame_index":0,"y":220,"x":250,"label":1}]

- **`box_prompts`** (`list<BoxPrompt>`, _optional_):
  Coordinates for boxes
  - Default: `[]`
  - Array of BoxPrompt
  - Examples: [{"x_max":500,"y_min":0,"x_min":300,"frame_index":0,"y_max":400}]

- **`apply_mask`** (`boolean`, _optional_):
  Apply the mask on the video.
  - Default: `false`

- **`boundingbox_zip`** (`boolean`, _optional_):
  Return per-frame bounding box overlays as a zip archive.
  - Default: `false`



**Required Parameters Example**:

```json
{
  "video_url": "https://drive.google.com/uc?id=1iOFYbNITYwrebBBp9kaEGhBndFSRLz8k"
}
```

**Full Example**:

```json
{
  "video_url": "https://drive.google.com/uc?id=1iOFYbNITYwrebBBp9kaEGhBndFSRLz8k",
  "prompts": [
    {
      "frame_index": 0,
      "y": 350,
      "x": 210,
      "label": 1
    },
    {
      "frame_index": 0,
      "y": 220,
      "x": 250,
      "label": 1
    }
  ],
  "box_prompts": [
    {
      "x_max": 500,
      "y_min": 0,
      "x_min": 300,
      "frame_index": 0,
      "y_max": 400
    }
  ]
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`File`, _required_):
  The segmented video.

- **`boundingbox_frames_zip`** (`File`, _optional_):
  Zip file containing per-frame bounding box overlays.



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
  --url https://fal.run/fal-ai/sam2/video \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "video_url": "https://drive.google.com/uc?id=1iOFYbNITYwrebBBp9kaEGhBndFSRLz8k"
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
    "fal-ai/sam2/video",
    arguments={
        "video_url": "https://drive.google.com/uc?id=1iOFYbNITYwrebBBp9kaEGhBndFSRLz8k"
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

const result = await fal.subscribe("fal-ai/sam2/video", {
  input: {
    video_url: "https://drive.google.com/uc?id=1iOFYbNITYwrebBBp9kaEGhBndFSRLz8k"
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

- [Model Playground](https://fal.ai/models/fal-ai/sam2/video)
- [API Documentation](https://fal.ai/models/fal-ai/sam2/video/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/sam2/video)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
