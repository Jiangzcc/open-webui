# Workflow Utilities Scale Video

> FFMPEG Utilities to Scale Videos


## Overview

- **Endpoint**: `https://fal.run/fal-ai/workflow-utilities/scale-video`
- **Model ID**: `fal-ai/workflow-utilities/scale-video`
- **Category**: video-to-video
- **Kind**: inference


## Pricing

- **Price**: $0.001 per compute seconds

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`video_url`** (`string`, _required_):
  URL of the video file to scale/resize. Height and Width of the video must be even numbers for compatibility with video codecs.
  - Examples: "https://storage.googleapis.com/falserverless/example_outputs/wan-25-i2v-output.mp4"

- **`width`** (`integer`, _optional_):
  Target width in pixels. If only width is provided, height is auto-calculated to preserve aspect ratio. At least one of width or height must be provided.
  - Range: `2` to `7680`
  - Examples: 1920, 3840, 1280

- **`height`** (`integer`, _optional_):
  Target height in pixels. If only height is provided, width is auto-calculated to preserve aspect ratio. At least one of width or height must be provided.
  - Range: `2` to `4320`
  - Examples: 1080, 2160, 720

- **`mode`** (`ModeEnum`, _optional_):
  Scaling mode. 'stretch' scales the video to the exact target dimensions (may distort aspect ratio). 'pad' scales to fit within the target dimensions while preserving aspect ratio, then pads with the chosen color to fill the remaining space (letterbox/pillarbox). 'crop' scales to cover the target dimensions while preserving aspect ratio, then center-crops to the exact target size. Default value: `"stretch"`
  - Default: `"stretch"`
  - Options: `"stretch"`, `"pad"`, `"crop"`

- **`pad_color`** (`PadColorEnum`, _optional_):
  Padding color when mode is 'pad'. Ignored for other modes. Default value: `"black"`
  - Default: `"black"`
  - Options: `"black"`, `"white"`, `"red"`, `"green"`, `"blue"`, `"gray"`

- **`codec`** (`CodecEnum`, _optional_):
  Video codec to use for encoding. libx264 (H.264) is widely compatible, libx265 (H.265/HEVC) offers better compression. Default value: `"libx264"`
  - Default: `"libx264"`
  - Options: `"libx264"`, `"libx265"`

- **`preset`** (`PresetEnum`, _optional_):
  Encoding speed preset. Slower presets give better compression but take longer. Default value: `"fast"`
  - Default: `"fast"`
  - Options: `"ultrafast"`, `"fast"`, `"medium"`, `"slow"`

- **`crf`** (`integer`, _optional_):
  Constant Rate Factor for quality (0-51). Lower values mean better quality and larger files. 18 is visually lossless for most content. Default value: `18`
  - Default: `18`
  - Range: `0` to `51`



**Required Parameters Example**:

```json
{
  "video_url": "https://storage.googleapis.com/falserverless/example_outputs/wan-25-i2v-output.mp4"
}
```

**Full Example**:

```json
{
  "video_url": "https://storage.googleapis.com/falserverless/example_outputs/wan-25-i2v-output.mp4",
  "width": 1920,
  "height": 1080,
  "mode": "stretch",
  "pad_color": "black",
  "codec": "libx264",
  "preset": "fast",
  "crf": 18
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`File`, _required_):
  The scaled/resized video
  - Examples: {"file_size":3456789,"file_name":"output.mp4","content_type":"video/mp4","url":"https://v3b.fal.media/files/b/monkey/scaled_output.mp4"}

- **`original_width`** (`integer`, _required_):
  Width of the original video in pixels
  - Examples: 1929

- **`original_height`** (`integer`, _required_):
  Height of the original video in pixels
  - Examples: 1082

- **`scaled_width`** (`integer`, _required_):
  Width of the output video in pixels
  - Examples: 1920

- **`scaled_height`** (`integer`, _required_):
  Height of the output video in pixels
  - Examples: 1080



**Example Response**:

```json
{
  "video": {
    "file_size": 3456789,
    "file_name": "output.mp4",
    "content_type": "video/mp4",
    "url": "https://v3b.fal.media/files/b/monkey/scaled_output.mp4"
  },
  "original_width": 1929,
  "original_height": 1082,
  "scaled_width": 1920,
  "scaled_height": 1080
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/workflow-utilities/scale-video \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "video_url": "https://storage.googleapis.com/falserverless/example_outputs/wan-25-i2v-output.mp4"
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
    "fal-ai/workflow-utilities/scale-video",
    arguments={
        "video_url": "https://storage.googleapis.com/falserverless/example_outputs/wan-25-i2v-output.mp4"
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

const result = await fal.subscribe("fal-ai/workflow-utilities/scale-video", {
  input: {
    video_url: "https://storage.googleapis.com/falserverless/example_outputs/wan-25-i2v-output.mp4"
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

- [Model Playground](https://fal.ai/models/fal-ai/workflow-utilities/scale-video)
- [API Documentation](https://fal.ai/models/fal-ai/workflow-utilities/scale-video/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/workflow-utilities/scale-video)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
