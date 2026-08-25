# Lucy Restyle

> Restyle videos up to 30 min long - maintaining maximum detail quality.


## Overview

- **Endpoint**: `https://fal.run/decart/lucy-restyle`
- **Model ID**: `decart/lucy-restyle`
- **Category**: video-to-video
- **Kind**: inference
**Tags**: video-edit



## Pricing

- **Price**: $0.01 per seconds

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _required_):
  Text description of the desired video content
  - Examples: "Make it psychedelic art style with trippy colors and patterns"

- **`video_url`** (`string`, _required_):
  URL of the video to edit
  - Examples: "https://v3b.fal.media/files/b/0a86729a/wIXfP8RYCtKBQAV9HPs7o_output.mp4"

- **`seed`** (`integer`, _optional_):
  Seed for video generation

- **`resolution`** (`ResolutionEnum`, _optional_):
  Resolution of the generated video Default value: `"720p"`
  - Default: `"720p"`
  - Options: `"720p"`

- **`enhance_prompt`** (`boolean`, _optional_):
  Whether to enhance the prompt for better results. Default value: `true`
  - Default: `true`

- **`sync_mode`** (`boolean`, _optional_):
  If set to true, the function will wait for the video to be generated
  and uploaded before returning the response. This will increase the
  latency of the function but it allows you to get the video directly
  in the response without going through the CDN.
  - Default: `false`



**Required Parameters Example**:

```json
{
  "prompt": "Make it psychedelic art style with trippy colors and patterns",
  "video_url": "https://v3b.fal.media/files/b/0a86729a/wIXfP8RYCtKBQAV9HPs7o_output.mp4"
}
```

**Full Example**:

```json
{
  "prompt": "Make it psychedelic art style with trippy colors and patterns",
  "video_url": "https://v3b.fal.media/files/b/0a86729a/wIXfP8RYCtKBQAV9HPs7o_output.mp4",
  "resolution": "720p",
  "enhance_prompt": true
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`File`, _required_):
  The generated video
  - Examples: "https://v3b.fal.media/files/b/0a86d478/2JM2_bD0iJOmfcKHUEudv_generated_video.mp4"



**Example Response**:

```json
{
  "video": "https://v3b.fal.media/files/b/0a86d478/2JM2_bD0iJOmfcKHUEudv_generated_video.mp4"
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/decart/lucy-restyle \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "Make it psychedelic art style with trippy colors and patterns",
     "video_url": "https://v3b.fal.media/files/b/0a86729a/wIXfP8RYCtKBQAV9HPs7o_output.mp4"
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
    "decart/lucy-restyle",
    arguments={
        "prompt": "Make it psychedelic art style with trippy colors and patterns",
        "video_url": "https://v3b.fal.media/files/b/0a86729a/wIXfP8RYCtKBQAV9HPs7o_output.mp4"
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

const result = await fal.subscribe("decart/lucy-restyle", {
  input: {
    prompt: "Make it psychedelic art style with trippy colors and patterns",
    video_url: "https://v3b.fal.media/files/b/0a86729a/wIXfP8RYCtKBQAV9HPs7o_output.mp4"
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

- [Model Playground](https://fal.ai/models/decart/lucy-restyle)
- [API Documentation](https://fal.ai/models/decart/lucy-restyle/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=decart/lucy-restyle)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
