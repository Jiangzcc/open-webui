# Veo 3.1

> Extend Veo-Created Videos up to 30 seconds


## Overview

- **Endpoint**: `https://fal.run/fal-ai/veo3.1/extend-video`
- **Model ID**: `fal-ai/veo3.1/extend-video`
- **Category**: video-to-video
- **Kind**: inference
**Tags**: extend-video



## Pricing

For every second of video you generated, you will be charged **$0.20** (audio off) or **$0.40** (audio on). For example, a **5s video** with audio on will cost **$2**.

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _required_):
  The text prompt describing how the video should be extended
  - Examples: "Continue the scene naturally, maintaining the same style and motion."

- **`aspect_ratio`** (`AspectRatioEnum`, _optional_):
  The aspect ratio of the generated video. Default value: `"auto"`
  - Default: `"auto"`
  - Options: `"auto"`, `"16:9"`, `"9:16"`

- **`duration`** (`string`, _optional_):
  The duration of the generated video. Default value: `"7s"`
  - Default: `"7s"`

- **`negative_prompt`** (`string`, _optional_):
  A negative prompt to guide the video generation.

- **`resolution`** (`string`, _optional_):
  The resolution of the generated video. Default value: `"720p"`
  - Default: `"720p"`

- **`generate_audio`** (`boolean`, _optional_):
  Whether to generate audio for the video. Default value: `true`
  - Default: `true`

- **`seed`** (`integer`, _optional_):
  The seed for the random number generator.

- **`auto_fix`** (`boolean`, _optional_):
  Whether to automatically attempt to fix prompts that fail content policy or other validation checks by rewriting them.
  - Default: `false`

- **`safety_tolerance`** (`SafetyToleranceEnum`, _optional_):
  The safety tolerance level for content moderation. 1 is the most strict (blocks most content), 6 is the least strict. Default value: `"4"`
  - Default: `"4"`
  - Options: `"1"`, `"2"`, `"3"`, `"4"`, `"5"`, `"6"`

- **`video_url`** (`string`, _required_):
  URL of the video to extend. The video should be 720p or 1080p resolution in 16:9 or 9:16 aspect ratio.
  - Examples: "https://v3b.fal.media/files/b/0a8670fe/pY8UGl4_C452wOm9XUBYO_9ae04df8771c4f3f979fa5cabeca6ada.mp4"



**Required Parameters Example**:

```json
{
  "prompt": "Continue the scene naturally, maintaining the same style and motion.",
  "video_url": "https://v3b.fal.media/files/b/0a8670fe/pY8UGl4_C452wOm9XUBYO_9ae04df8771c4f3f979fa5cabeca6ada.mp4"
}
```

**Full Example**:

```json
{
  "prompt": "Continue the scene naturally, maintaining the same style and motion.",
  "aspect_ratio": "auto",
  "duration": "7s",
  "resolution": "720p",
  "generate_audio": true,
  "safety_tolerance": "4",
  "video_url": "https://v3b.fal.media/files/b/0a8670fe/pY8UGl4_C452wOm9XUBYO_9ae04df8771c4f3f979fa5cabeca6ada.mp4"
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`File`, _required_):
  The extended video.
  - Examples: {"url":"https://v3b.fal.media/files/b/0a86711b/B_Z96VS4X9Dfd4M5ArB4H_c666e63f729f4a8fa1145c6727cef97d.mp4"}



**Example Response**:

```json
{
  "video": {
    "url": "https://v3b.fal.media/files/b/0a86711b/B_Z96VS4X9Dfd4M5ArB4H_c666e63f729f4a8fa1145c6727cef97d.mp4"
  }
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/veo3.1/extend-video \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "Continue the scene naturally, maintaining the same style and motion.",
     "video_url": "https://v3b.fal.media/files/b/0a8670fe/pY8UGl4_C452wOm9XUBYO_9ae04df8771c4f3f979fa5cabeca6ada.mp4"
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
    "fal-ai/veo3.1/extend-video",
    arguments={
        "prompt": "Continue the scene naturally, maintaining the same style and motion.",
        "video_url": "https://v3b.fal.media/files/b/0a8670fe/pY8UGl4_C452wOm9XUBYO_9ae04df8771c4f3f979fa5cabeca6ada.mp4"
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

const result = await fal.subscribe("fal-ai/veo3.1/extend-video", {
  input: {
    prompt: "Continue the scene naturally, maintaining the same style and motion.",
    video_url: "https://v3b.fal.media/files/b/0a8670fe/pY8UGl4_C452wOm9XUBYO_9ae04df8771c4f3f979fa5cabeca6ada.mp4"
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

- [Model Playground](https://fal.ai/models/fal-ai/veo3.1/extend-video)
- [API Documentation](https://fal.ai/models/fal-ai/veo3.1/extend-video/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/veo3.1/extend-video)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
