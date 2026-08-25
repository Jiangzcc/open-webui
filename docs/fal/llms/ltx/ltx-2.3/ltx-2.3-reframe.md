# Ltx 2.3 

>  LTX-2.3 Reframe converts your videos to any aspect ratio without destructive cropping. It intelligently recenters the original footage and generatively fills the newly exposed areas with content that seamlessly matches the scene, so the result looks like it was shot natively in the target format. Turn landscape footage into vertical 9:16 for social, square 1:1 for feeds, or anything in between. Supports videos up to 60 seconds, with 720p and 1080p outputs across 1:1, 4:5, 5:4, 9:16 and 16:9.


## Overview

- **Endpoint**: `https://fal.run/fal-ai/ltx-2.3/reframe`
- **Model ID**: `fal-ai/ltx-2.3/reframe`
- **Category**: video-to-video
- **Kind**: inference
**Tags**: reframe, size, 



## Pricing

Your request will cost $0.10 per second for 720p output or $0.20 per second for 1080p output, billed on the duration of your input video. For example, reframing a 10-second video costs $1.00 at 720p or $2.00 at 1080p.

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`video_url`** (`string`, _required_):
  The URL of the video to reframe. Must be publicly accessible or a base64 data URI. The video is re-cropped to the target aspect ratio and the newly exposed areas are filled with generated content that matches the original. Max duration 60 seconds.
  - Examples: "https://storage.googleapis.com/falserverless/example_outputs/ltxv-2-t2v-output.mp4"

- **`aspect_ratio`** (`AspectRatioEnum`, _optional_):
  The target aspect ratio to reframe the video to. Default value: `"16:9"`
  - Default: `"16:9"`
  - Options: `"1:1"`, `"4:5"`, `"5:4"`, `"9:16"`, `"16:9"`

- **`resolution`** (`ResolutionEnum`, _optional_):
  The target output resolution tier. Combined with the aspect ratio to determine the output size. Default value: `"1080p"`
  - Default: `"1080p"`
  - Options: `"720p"`, `"1080p"`



**Required Parameters Example**:

```json
{
  "video_url": "https://storage.googleapis.com/falserverless/example_outputs/ltxv-2-t2v-output.mp4"
}
```

**Full Example**:

```json
{
  "video_url": "https://storage.googleapis.com/falserverless/example_outputs/ltxv-2-t2v-output.mp4",
  "aspect_ratio": "16:9",
  "resolution": "1080p"
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`VideoFile`, _required_):
  The reframed video file
  - Examples: {"file_name":"ltxv-2-3-reframe-output.mp4","content_type":"video/mp4","url":"https://v3b.fal.media/files/b/0a90e00f/xvl9SlF6b7a8327wKJDvm_JW6crfr3.mp4"}



**Example Response**:

```json
{
  "video": {
    "file_name": "ltxv-2-3-reframe-output.mp4",
    "content_type": "video/mp4",
    "url": "https://v3b.fal.media/files/b/0a90e00f/xvl9SlF6b7a8327wKJDvm_JW6crfr3.mp4"
  }
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/ltx-2.3/reframe \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "video_url": "https://storage.googleapis.com/falserverless/example_outputs/ltxv-2-t2v-output.mp4"
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
    "fal-ai/ltx-2.3/reframe",
    arguments={
        "video_url": "https://storage.googleapis.com/falserverless/example_outputs/ltxv-2-t2v-output.mp4"
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

const result = await fal.subscribe("fal-ai/ltx-2.3/reframe", {
  input: {
    video_url: "https://storage.googleapis.com/falserverless/example_outputs/ltxv-2-t2v-output.mp4"
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

- [Model Playground](https://fal.ai/models/fal-ai/ltx-2.3/reframe)
- [API Documentation](https://fal.ai/models/fal-ai/ltx-2.3/reframe/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/ltx-2.3/reframe)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
