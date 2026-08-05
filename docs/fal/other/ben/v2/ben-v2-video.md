# Ben-Video-Bg-Rm

> A model for high quality and smooth background removal for videos.


## Overview

- **Endpoint**: `https://fal.run/fal-ai/ben/v2/video`
- **Model ID**: `fal-ai/ben/v2/video`
- **Category**: video-to-video
- **Kind**: inference
**Tags**: segmentation, background removal



## Pricing

- **Price**: $0.001 per megapixels

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`video_url`** (`string`, _required_):
  URL of video to be used for background removal.
  - Examples: "https://storage.googleapis.com/falserverless/gallery/Ben2/100063-video-2160.mp4"

- **`background_color`** (`array`, _optional_):
  Optional RGB values (0-255) for the background color. If not provided, the background will be transparent. For ex: [0, 0, 0]

- **`output_format`** (`OutputFormatEnum`, _optional_):
  Output video format. Use "webm" for true transparency support (VP9 codec with alpha channel). MP4 format does not support transparency and will render transparent areas as black. Default value: `"mp4"`
  - Default: `"mp4"`
  - Options: `"mp4"`, `"webm"`

- **`seed`** (`integer`, _optional_):
  Random seed for reproducible generation.



**Required Parameters Example**:

```json
{
  "video_url": "https://storage.googleapis.com/falserverless/gallery/Ben2/100063-video-2160.mp4"
}
```

**Full Example**:

```json
{
  "video_url": "https://storage.googleapis.com/falserverless/gallery/Ben2/100063-video-2160.mp4",
  "output_format": "mp4"
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`File`, _required_):
  The generated video file.
  - Examples: {"url":"https://storage.googleapis.com/falserverless/gallery/Ben2/foreground.mp4","content_type":"video/mp4"}

- **`seed`** (`integer`, _required_):
  Seed of the generated Image. It will be the same value of the one passed in the
  input or the randomly generated that was used in case none was passed.



**Example Response**:

```json
{
  "video": {
    "url": "https://storage.googleapis.com/falserverless/gallery/Ben2/foreground.mp4",
    "content_type": "video/mp4"
  }
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/ben/v2/video \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "video_url": "https://storage.googleapis.com/falserverless/gallery/Ben2/100063-video-2160.mp4"
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
    "fal-ai/ben/v2/video",
    arguments={
        "video_url": "https://storage.googleapis.com/falserverless/gallery/Ben2/100063-video-2160.mp4"
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

const result = await fal.subscribe("fal-ai/ben/v2/video", {
  input: {
    video_url: "https://storage.googleapis.com/falserverless/gallery/Ben2/100063-video-2160.mp4"
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

- [Model Playground](https://fal.ai/models/fal-ai/ben/v2/video)
- [API Documentation](https://fal.ai/models/fal-ai/ben/v2/video/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/ben/v2/video)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
