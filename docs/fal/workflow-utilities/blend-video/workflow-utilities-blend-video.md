# Workflow Utilities Blend Video

> FFMPEG Utility for Blending Videos


## Overview

- **Endpoint**: `https://fal.run/fal-ai/workflow-utilities/blend-video`
- **Model ID**: `fal-ai/workflow-utilities/blend-video`
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


- **`top_video_url`** (`string`, _required_):
  URL of the top layer video
  - Examples: "https://storage.googleapis.com/falserverless/example_outputs/wan-25-i2v-output.mp4"

- **`bottom_video_url`** (`string`, _required_):
  URL of the bottom layer video
  - Examples: "https://storage.googleapis.com/falserverless/model_tests/kling/kling-v2.5-turbo-pro-image-to-video-output.mp4"

- **`blend_mode`** (`BlendModeEnum`, _optional_):
  Blend mode to use for combining the videos Default value: `"overlay"`
  - Default: `"overlay"`
  - Options: `"addition"`, `"average"`, `"burn"`, `"darken"`, `"difference"`, `"divide"`, `"dodge"`, `"exclusion"`, `"grainextract"`, `"grainmerge"`, `"hardlight"`, `"lighten"`, `"multiply"`, `"negation"`, `"normal"`, `"overlay"`, `"phoenix"`, `"pinlight"`, `"reflect"`, `"screen"`, `"softlight"`, `"subtract"`, `"vividlight"`

- **`opacity`** (`float`, _optional_):
  Opacity of the top layer (0.0-1.0) Default value: `1`
  - Default: `1`
  - Range: `0` to `1`

- **`shortest`** (`boolean`, _optional_):
  End output when the shortest input ends Default value: `true`
  - Default: `true`



**Required Parameters Example**:

```json
{
  "top_video_url": "https://storage.googleapis.com/falserverless/example_outputs/wan-25-i2v-output.mp4",
  "bottom_video_url": "https://storage.googleapis.com/falserverless/model_tests/kling/kling-v2.5-turbo-pro-image-to-video-output.mp4"
}
```

**Full Example**:

```json
{
  "top_video_url": "https://storage.googleapis.com/falserverless/example_outputs/wan-25-i2v-output.mp4",
  "bottom_video_url": "https://storage.googleapis.com/falserverless/model_tests/kling/kling-v2.5-turbo-pro-image-to-video-output.mp4",
  "blend_mode": "overlay",
  "opacity": 1,
  "shortest": true
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`File`, _required_):
  The blended video output
  - Examples: {"file_size":3886177,"file_name":"blended_output.mp4","content_type":"video/mp4","url":"https://v3b.fal.media/files/b/monkey/blended_output.mp4"}



**Example Response**:

```json
{
  "video": {
    "file_size": 3886177,
    "file_name": "blended_output.mp4",
    "content_type": "video/mp4",
    "url": "https://v3b.fal.media/files/b/monkey/blended_output.mp4"
  }
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/workflow-utilities/blend-video \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "top_video_url": "https://storage.googleapis.com/falserverless/example_outputs/wan-25-i2v-output.mp4",
     "bottom_video_url": "https://storage.googleapis.com/falserverless/model_tests/kling/kling-v2.5-turbo-pro-image-to-video-output.mp4"
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
    "fal-ai/workflow-utilities/blend-video",
    arguments={
        "top_video_url": "https://storage.googleapis.com/falserverless/example_outputs/wan-25-i2v-output.mp4",
        "bottom_video_url": "https://storage.googleapis.com/falserverless/model_tests/kling/kling-v2.5-turbo-pro-image-to-video-output.mp4"
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

const result = await fal.subscribe("fal-ai/workflow-utilities/blend-video", {
  input: {
    top_video_url: "https://storage.googleapis.com/falserverless/example_outputs/wan-25-i2v-output.mp4",
    bottom_video_url: "https://storage.googleapis.com/falserverless/model_tests/kling/kling-v2.5-turbo-pro-image-to-video-output.mp4"
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

- [Model Playground](https://fal.ai/models/fal-ai/workflow-utilities/blend-video)
- [API Documentation](https://fal.ai/models/fal-ai/workflow-utilities/blend-video/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/workflow-utilities/blend-video)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
