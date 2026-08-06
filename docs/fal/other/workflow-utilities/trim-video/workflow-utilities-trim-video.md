# Workflow Utilities Trim Video

> FFMPEG Utility for Trim Video


## Overview

- **Endpoint**: `https://fal.run/fal-ai/workflow-utilities/trim-video`
- **Model ID**: `fal-ai/workflow-utilities/trim-video`
- **Category**: video-to-video
- **Kind**: inference
**Tags**: video-to-video



## Pricing

- **Price**: $0.001 per compute seconds

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`video_url`** (`string`, _required_):
  URL of the video file to trim
  - Examples: "https://storage.googleapis.com/falserverless/example_outputs/wan-25-i2v-output.mp4"

- **`start_time`** (`float`, _optional_):
  Start time in seconds Default value: `1`
  - Default: `1`

- **`end_time`** (`float`, _optional_):
  End time in seconds. If not provided, uses duration instead.
  - Examples: 3

- **`duration`** (`float`, _optional_):
  Duration in seconds from start_time. Ignored if end_time is provided. Default value: `2`
  - Default: `2`



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
  "start_time": 1,
  "end_time": 3,
  "duration": 2
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`File`, _required_):
  The trimmed video
  - Examples: {"file_size":2550671,"file_name":"output.mp4","content_type":"application/octet-stream","url":"https://v3b.fal.media/files/b/0a8dcc60/sIg2GuYYYrmYAa2lUVgum_output.mp4"}

- **`original_duration`** (`float`, _required_):
  Duration of the original video in seconds
  - Examples: 5.041667

- **`trimmed_duration`** (`float`, _required_):
  Duration of the trimmed video in seconds
  - Examples: 2



**Example Response**:

```json
{
  "video": {
    "file_size": 2550671,
    "file_name": "output.mp4",
    "content_type": "application/octet-stream",
    "url": "https://v3b.fal.media/files/b/0a8dcc60/sIg2GuYYYrmYAa2lUVgum_output.mp4"
  },
  "original_duration": 5.041667,
  "trimmed_duration": 2
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/workflow-utilities/trim-video \
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
    "fal-ai/workflow-utilities/trim-video",
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

const result = await fal.subscribe("fal-ai/workflow-utilities/trim-video", {
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

- [Model Playground](https://fal.ai/models/fal-ai/workflow-utilities/trim-video)
- [API Documentation](https://fal.ai/models/fal-ai/workflow-utilities/trim-video/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/workflow-utilities/trim-video)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
