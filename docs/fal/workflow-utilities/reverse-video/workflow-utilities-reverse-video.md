# Workflow Utilities Reverse Video

> FFMPEG Utility to Reverse Videos


## Overview

- **Endpoint**: `https://fal.run/fal-ai/workflow-utilities/reverse-video`
- **Model ID**: `fal-ai/workflow-utilities/reverse-video`
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
  URL of the video file to reverse
  - Examples: "https://storage.googleapis.com/falserverless/example_outputs/wan-25-i2v-output.mp4"



**Required Parameters Example**:

```json
{
  "video_url": "https://storage.googleapis.com/falserverless/example_outputs/wan-25-i2v-output.mp4"
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`File`, _required_):
  The reversed video
  - Examples: {"file_size":3456789,"file_name":"output.mp4","content_type":"video/mp4","url":"ttps://v3b.fal.media/files/b/0a8f1bc2/HZdek_1QHprZFiE-46DyO_output.mp4"}



**Example Response**:

```json
{
  "video": {
    "file_size": 3456789,
    "file_name": "output.mp4",
    "content_type": "video/mp4",
    "url": "ttps://v3b.fal.media/files/b/0a8f1bc2/HZdek_1QHprZFiE-46DyO_output.mp4"
  }
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/workflow-utilities/reverse-video \
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
    "fal-ai/workflow-utilities/reverse-video",
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

const result = await fal.subscribe("fal-ai/workflow-utilities/reverse-video", {
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

- [Model Playground](https://fal.ai/models/fal-ai/workflow-utilities/reverse-video)
- [API Documentation](https://fal.ai/models/fal-ai/workflow-utilities/reverse-video/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/workflow-utilities/reverse-video)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
