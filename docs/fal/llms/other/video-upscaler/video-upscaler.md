# Video Upscaler

> The video upscaler endpoint uses RealESRGAN on each frame of the input video to upscale the video to a higher resolution.


## Overview

- **Endpoint**: `https://fal.run/fal-ai/video-upscaler`
- **Model ID**: `fal-ai/video-upscaler`
- **Category**: video-to-video
- **Kind**: inference
**Tags**: video generation, video to video, ai video, high fidelity motion



## Pricing

- **Price**: $0.0008 per megapixels

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`video_url`** (`string`, _required_):
  The URL of the video to upscale
  - Examples: "https://storage.googleapis.com/falserverless/videos/_o3VmzjOytBwRjCVPFX6i_output.mp4"

- **`scale`** (`float`, _optional_):
  The scale factor Default value: `2`
  - Default: `2`
  - Range: `1` to `8`



**Required Parameters Example**:

```json
{
  "video_url": "https://storage.googleapis.com/falserverless/videos/_o3VmzjOytBwRjCVPFX6i_output.mp4"
}
```

**Full Example**:

```json
{
  "video_url": "https://storage.googleapis.com/falserverless/videos/_o3VmzjOytBwRjCVPFX6i_output.mp4",
  "scale": 2
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`File`, _required_):
  The stitched video
  - Examples: {"content_type":"video/mp4","url":"https://storage.googleapis.com/falserverless/videos/h0jgPaO6AJAbyrsNYNbGl_upscaled_video.mp4"}



**Example Response**:

```json
{
  "video": {
    "content_type": "video/mp4",
    "url": "https://storage.googleapis.com/falserverless/videos/h0jgPaO6AJAbyrsNYNbGl_upscaled_video.mp4"
  }
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/video-upscaler \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "video_url": "https://storage.googleapis.com/falserverless/videos/_o3VmzjOytBwRjCVPFX6i_output.mp4"
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
    "fal-ai/video-upscaler",
    arguments={
        "video_url": "https://storage.googleapis.com/falserverless/videos/_o3VmzjOytBwRjCVPFX6i_output.mp4"
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

const result = await fal.subscribe("fal-ai/video-upscaler", {
  input: {
    video_url: "https://storage.googleapis.com/falserverless/videos/_o3VmzjOytBwRjCVPFX6i_output.mp4"
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

- [Model Playground](https://fal.ai/models/fal-ai/video-upscaler)
- [API Documentation](https://fal.ai/models/fal-ai/video-upscaler/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/video-upscaler)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
