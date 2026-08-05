# Video Background Removal

> Remove background from videos filmed using chromakey, with automatic green spill suppression for clean, professional edges.


## Overview

- **Endpoint**: `https://fal.run/veed/video-background-removal/green-screen`
- **Model ID**: `veed/video-background-removal/green-screen`
- **Category**: video-to-video
- **Kind**: inference


## Pricing

Your request will cost **$0.025** per 30 frames.

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`video_url`** (`string`, _required_)
  - Examples: "https://v3b.fal.media/files/b/0a849c38/zoA0frujpZUkj07NtXytv_jessica.mp4"

- **`output_codec`** (`OutputCodecEnum`, _optional_):
  Single VP9 video with alpha channel or two videos (rgb and alpha) in H264 format. H264 is recommended for better RGB quality. Default value: `"vp9"`
  - Default: `"vp9"`
  - Options: `"vp9"`, `"h264"`

- **`spill_suppression_strength`** (`float`, _optional_):
  Increase the value if green spots remain in the video, decrease if color changes are noticed on the extracted subject. Default value: `0.8`
  - Default: `0.8`
  - Range: `0` to `1`



**Required Parameters Example**:

```json
{
  "video_url": "https://v3b.fal.media/files/b/0a849c38/zoA0frujpZUkj07NtXytv_jessica.mp4"
}
```

**Full Example**:

```json
{
  "video_url": "https://v3b.fal.media/files/b/0a849c38/zoA0frujpZUkj07NtXytv_jessica.mp4",
  "output_codec": "vp9",
  "spill_suppression_strength": 0.8
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`list<File>`, _required_)
  - Array of File
  - Examples: [{"content_type":"video/webm","url":"https://v3b.fal.media/files/b/0a849c48/MFOmvAhK4vvUsFsMVmw0P_output.webm"}]



**Example Response**:

```json
{
  "video": [
    {
      "content_type": "video/webm",
      "url": "https://v3b.fal.media/files/b/0a849c48/MFOmvAhK4vvUsFsMVmw0P_output.webm"
    }
  ]
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/veed/video-background-removal/green-screen \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "video_url": "https://v3b.fal.media/files/b/0a849c38/zoA0frujpZUkj07NtXytv_jessica.mp4"
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
    "veed/video-background-removal/green-screen",
    arguments={
        "video_url": "https://v3b.fal.media/files/b/0a849c38/zoA0frujpZUkj07NtXytv_jessica.mp4"
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

const result = await fal.subscribe("veed/video-background-removal/green-screen", {
  input: {
    video_url: "https://v3b.fal.media/files/b/0a849c38/zoA0frujpZUkj07NtXytv_jessica.mp4"
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

- [Model Playground](https://fal.ai/models/veed/video-background-removal/green-screen)
- [API Documentation](https://fal.ai/models/veed/video-background-removal/green-screen/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=veed/video-background-removal/green-screen)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
