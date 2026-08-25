# LTX Video 2.3 Pro

> LTX-2.3 is a high-quality, fast AI video model available in Pro and Fast variants for text-to-video, image-to-video, and audio-to-video.


## Overview

- **Endpoint**: `https://fal.run/fal-ai/ltx-2.3/extend-video`
- **Model ID**: `fal-ai/ltx-2.3/extend-video`
- **Category**: video-to-video
- **Kind**: inference
**Tags**: stylized, transform, lipsync



## Pricing

Your request will cost **$0.10 per second.**

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`video_url`** (`string`, _required_):
  The URL of the video to extend
  - Examples: "https://v3b.fal.media/files/b/0a90e01f/SWYdQyTBCPWYOLgfg5Jw2_004_video.mp4"

- **`prompt`** (`string`, _optional_):
  Description of what should happen in the extended portion of the video.
  - Examples: "Continue the motion smoothly"

- **`duration`** (`float`, _optional_):
  Duration in seconds to extend the video. Minimum 2 seconds, maximum 20 seconds. Default value: `5`
  - Default: `5`
  - Range: `2` to `20`

- **`mode`** (`ModeEnum`, _optional_):
  Where to extend the video: 'end' extends at the end, 'start' extends at the beginning. Default value: `"end"`
  - Default: `"end"`
  - Options: `"start"`, `"end"`

- **`context`** (`float`, _optional_):
  Number of seconds from the input video to use as context for the extension (minimum 1 second, maximum 20 seconds). If not provided, defaults to maximize available context within the 505 frame limit.
  - Range: `1` to `20`



**Required Parameters Example**:

```json
{
  "video_url": "https://v3b.fal.media/files/b/0a90e01f/SWYdQyTBCPWYOLgfg5Jw2_004_video.mp4"
}
```

**Full Example**:

```json
{
  "video_url": "https://v3b.fal.media/files/b/0a90e01f/SWYdQyTBCPWYOLgfg5Jw2_004_video.mp4",
  "prompt": "Continue the motion smoothly",
  "duration": 5,
  "mode": "end"
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`VideoFile`, _required_):
  The extended video file
  - Examples: {"file_name":"sQT2ORTL4ISEeLv3mRdF0_rGO62gwz.mp4","content_type":"video/mp4","url":"https://v3b.fal.media/files/b/0a90e020/sQT2ORTL4ISEeLv3mRdF0_rGO62gwz.mp4"}



**Example Response**:

```json
{
  "video": {
    "file_name": "sQT2ORTL4ISEeLv3mRdF0_rGO62gwz.mp4",
    "content_type": "video/mp4",
    "url": "https://v3b.fal.media/files/b/0a90e020/sQT2ORTL4ISEeLv3mRdF0_rGO62gwz.mp4"
  }
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/ltx-2.3/extend-video \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "video_url": "https://v3b.fal.media/files/b/0a90e01f/SWYdQyTBCPWYOLgfg5Jw2_004_video.mp4"
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
    "fal-ai/ltx-2.3/extend-video",
    arguments={
        "video_url": "https://v3b.fal.media/files/b/0a90e01f/SWYdQyTBCPWYOLgfg5Jw2_004_video.mp4"
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

const result = await fal.subscribe("fal-ai/ltx-2.3/extend-video", {
  input: {
    video_url: "https://v3b.fal.media/files/b/0a90e01f/SWYdQyTBCPWYOLgfg5Jw2_004_video.mp4"
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

- [Model Playground](https://fal.ai/models/fal-ai/ltx-2.3/extend-video)
- [API Documentation](https://fal.ai/models/fal-ai/ltx-2.3/extend-video/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/ltx-2.3/extend-video)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
