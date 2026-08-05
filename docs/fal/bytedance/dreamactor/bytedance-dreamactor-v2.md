# Bytedance Dreamactor V2

> Transfer motion from a video to characters in an image using Dreamactor v2. Great performance for non-human and multiple characters


## Overview

- **Endpoint**: `https://fal.run/fal-ai/bytedance/dreamactor/v2`
- **Model ID**: `fal-ai/bytedance/dreamactor/v2`
- **Category**: video-to-video
- **Kind**: inference
**Tags**: motion-control, dreamactor



## Pricing

- **Price**: $0.05 per seconds

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`image_url`** (`string`, _required_):
  The URL of the reference image to animate. Supports real people, animation, pets, etc. Format: jpeg, jpg or png. Max size: 4.7 MB. Resolution: between 480x480 and 1920x1080 (larger images will be proportionally reduced).
  - Examples: "https://storage.googleapis.com/falserverless/example_inputs/omnihuman.png"

- **`video_url`** (`string`, _required_):
  The URL of the driving template video providing motion, facial expressions, and lip movement reference. Max duration: 30 seconds. Format: mp4, mov or webm. Resolution: between 200x200 and 2048x1440. Supports full face and body driving.
  - Examples: "https://storage.googleapis.com/falserverless/example_outputs/omnihuman_output.mp4"

- **`trim_first_second`** (`boolean`, _optional_):
  Whether to crop the first second of the output video. The output has a 1-second transition at the beginning; enable this to remove it. Default value: `true`
  - Default: `true`



**Required Parameters Example**:

```json
{
  "image_url": "https://storage.googleapis.com/falserverless/example_inputs/omnihuman.png",
  "video_url": "https://storage.googleapis.com/falserverless/example_outputs/omnihuman_output.mp4"
}
```

**Full Example**:

```json
{
  "image_url": "https://storage.googleapis.com/falserverless/example_inputs/omnihuman.png",
  "video_url": "https://storage.googleapis.com/falserverless/example_outputs/omnihuman_output.mp4",
  "trim_first_second": true
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`File`, _required_):
  Generated video file.
  - Examples: {"url":"https://v3b.fal.media/files/b/0a8d6313/ONsZwYeJrFqi1W1jbnfYF_9HU7tPvX1hUlMMxXCepTz_video%20(1)%20(1).mp4"}



**Example Response**:

```json
{
  "video": {
    "url": "https://v3b.fal.media/files/b/0a8d6313/ONsZwYeJrFqi1W1jbnfYF_9HU7tPvX1hUlMMxXCepTz_video%20(1)%20(1).mp4"
  }
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/bytedance/dreamactor/v2 \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "image_url": "https://storage.googleapis.com/falserverless/example_inputs/omnihuman.png",
     "video_url": "https://storage.googleapis.com/falserverless/example_outputs/omnihuman_output.mp4"
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
    "fal-ai/bytedance/dreamactor/v2",
    arguments={
        "image_url": "https://storage.googleapis.com/falserverless/example_inputs/omnihuman.png",
        "video_url": "https://storage.googleapis.com/falserverless/example_outputs/omnihuman_output.mp4"
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

const result = await fal.subscribe("fal-ai/bytedance/dreamactor/v2", {
  input: {
    image_url: "https://storage.googleapis.com/falserverless/example_inputs/omnihuman.png",
    video_url: "https://storage.googleapis.com/falserverless/example_outputs/omnihuman_output.mp4"
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

- [Model Playground](https://fal.ai/models/fal-ai/bytedance/dreamactor/v2)
- [API Documentation](https://fal.ai/models/fal-ai/bytedance/dreamactor/v2/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/bytedance/dreamactor/v2)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
