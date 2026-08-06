# Video Background Removal

> Remove background from any video with people and objects. No green screen needed.


## Overview

- **Endpoint**: `https://fal.run/veed/video-background-removal/fast`
- **Model ID**: `veed/video-background-removal/fast`
- **Category**: video-to-video
- **Kind**: inference


## Pricing

Your request will cost **$0.012** per 30 frames (Refine Foreground Edges: ON) / **$0.008** cents (Refine: OFF).

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`video_url`** (`string`, _required_)
  - Examples: "https://v3b.fal.media/files/b/0a8479a0/3ngPszofrNpEvPaL9P5xR_generated.mp4"

- **`output_codec`** (`OutputCodecEnum`, _optional_):
  Single VP9 video with alpha channel or two videos (rgb and alpha) in H264 format. H264 is recommended for better RGB quality. Default value: `"vp9"`
  - Default: `"vp9"`
  - Options: `"vp9"`, `"h264"`

- **`refine_foreground_edges`** (`boolean`, _optional_):
  Improves the quality of the extracted object's edges. Default value: `true`
  - Default: `true`

- **`subject_is_person`** (`boolean`, _optional_):
  Set to False if the subject is not a person. Default value: `true`
  - Default: `true`



**Required Parameters Example**:

```json
{
  "video_url": "https://v3b.fal.media/files/b/0a8479a0/3ngPszofrNpEvPaL9P5xR_generated.mp4"
}
```

**Full Example**:

```json
{
  "video_url": "https://v3b.fal.media/files/b/0a8479a0/3ngPszofrNpEvPaL9P5xR_generated.mp4",
  "output_codec": "vp9",
  "refine_foreground_edges": true,
  "subject_is_person": true
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`list<File>`, _required_)
  - Array of File
  - Examples: [{"content_type":"video/webm","url":"https://v3b.fal.media/files/b/0a8479a7/mdr5_b7CqeDmZROCLkp7i_output.webm"}]



**Example Response**:

```json
{
  "video": [
    {
      "content_type": "video/webm",
      "url": "https://v3b.fal.media/files/b/0a8479a7/mdr5_b7CqeDmZROCLkp7i_output.webm"
    }
  ]
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/veed/video-background-removal/fast \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "video_url": "https://v3b.fal.media/files/b/0a8479a0/3ngPszofrNpEvPaL9P5xR_generated.mp4"
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
    "veed/video-background-removal/fast",
    arguments={
        "video_url": "https://v3b.fal.media/files/b/0a8479a0/3ngPszofrNpEvPaL9P5xR_generated.mp4"
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

const result = await fal.subscribe("veed/video-background-removal/fast", {
  input: {
    video_url: "https://v3b.fal.media/files/b/0a8479a0/3ngPszofrNpEvPaL9P5xR_generated.mp4"
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

- [Model Playground](https://fal.ai/models/veed/video-background-removal/fast)
- [API Documentation](https://fal.ai/models/veed/video-background-removal/fast/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=veed/video-background-removal/fast)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
