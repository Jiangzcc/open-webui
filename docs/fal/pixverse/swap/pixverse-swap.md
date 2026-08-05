# PixVerse Swap

> Generate high quality video clips by swapping person, objects and background using Pixverse Swap.


## Overview

- **Endpoint**: `https://fal.run/fal-ai/pixverse/swap`
- **Model ID**: `fal-ai/pixverse/swap`
- **Category**: image-to-video
- **Kind**: inference


## Pricing

For 5s video your request will cost **$0.15** for 360p and 540p, **$0.2** for 720p and **$0.4** for 1080p. If input video duration is greater than 5 s the cost will double. For **$1** you can run this model with approximately 2 times.

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`video_url`** (`string`, _required_):
  URL of the external video to swap
  - Examples: "https://v3b.fal.media/files/b/lion/k_RpEIZ4YZtwZklzXz7Gb_output.mp4"

- **`mode`** (`ModeEnum`, _optional_):
  The swap mode to use Default value: `"person"`
  - Default: `"person"`
  - Options: `"person"`, `"object"`, `"background"`

- **`keyframe_id`** (`integer`, _optional_):
  The keyframe ID to use for face/object mapping. The input video is normalized to 24 FPS before processing, so keyframe 1 = first frame, keyframe 24 = 1 second in, etc. Valid range: 1 to (duration_seconds * 24). Default value: `1`
  - Default: `1`

- **`image_url`** (`string`, _required_):
  URL of the target image for swapping
  - Examples: "https://v3b.fal.media/files/b/elephant/Lu7lo2dpxVPD-NrNZzx42_56dc797a1f764c98a4f075a8c0332bf0.jpg"

- **`resolution`** (`ResolutionEnum`, _optional_):
  The output resolution (1080p not supported) Default value: `"720p"`
  - Default: `"720p"`
  - Options: `"360p"`, `"540p"`, `"720p"`

- **`seed`** (`integer`, _optional_):
  Random seed for generation

- **`original_sound_switch`** (`boolean`, _optional_):
  Whether to keep the original audio Default value: `true`
  - Default: `true`



**Required Parameters Example**:

```json
{
  "video_url": "https://v3b.fal.media/files/b/lion/k_RpEIZ4YZtwZklzXz7Gb_output.mp4",
  "image_url": "https://v3b.fal.media/files/b/elephant/Lu7lo2dpxVPD-NrNZzx42_56dc797a1f764c98a4f075a8c0332bf0.jpg"
}
```

**Full Example**:

```json
{
  "video_url": "https://v3b.fal.media/files/b/lion/k_RpEIZ4YZtwZklzXz7Gb_output.mp4",
  "mode": "person",
  "keyframe_id": 1,
  "image_url": "https://v3b.fal.media/files/b/elephant/Lu7lo2dpxVPD-NrNZzx42_56dc797a1f764c98a4f075a8c0332bf0.jpg",
  "resolution": "720p",
  "original_sound_switch": true
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`File`, _required_):
  The generated swapped video
  - Examples: {"file_size":1234567,"file_name":"output.mp4","content_type":"video/mp4","url":"https://v3b.fal.media/files/b/elephant/BdQvPf9T6puy3Co1_ZXeu_output.mp4"}



**Example Response**:

```json
{
  "video": {
    "file_size": 1234567,
    "file_name": "output.mp4",
    "content_type": "video/mp4",
    "url": "https://v3b.fal.media/files/b/elephant/BdQvPf9T6puy3Co1_ZXeu_output.mp4"
  }
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/pixverse/swap \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "video_url": "https://v3b.fal.media/files/b/lion/k_RpEIZ4YZtwZklzXz7Gb_output.mp4",
     "image_url": "https://v3b.fal.media/files/b/elephant/Lu7lo2dpxVPD-NrNZzx42_56dc797a1f764c98a4f075a8c0332bf0.jpg"
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
    "fal-ai/pixverse/swap",
    arguments={
        "video_url": "https://v3b.fal.media/files/b/lion/k_RpEIZ4YZtwZklzXz7Gb_output.mp4",
        "image_url": "https://v3b.fal.media/files/b/elephant/Lu7lo2dpxVPD-NrNZzx42_56dc797a1f764c98a4f075a8c0332bf0.jpg"
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

const result = await fal.subscribe("fal-ai/pixverse/swap", {
  input: {
    video_url: "https://v3b.fal.media/files/b/lion/k_RpEIZ4YZtwZklzXz7Gb_output.mp4",
    image_url: "https://v3b.fal.media/files/b/elephant/Lu7lo2dpxVPD-NrNZzx42_56dc797a1f764c98a4f075a8c0332bf0.jpg"
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

- [Model Playground](https://fal.ai/models/fal-ai/pixverse/swap)
- [API Documentation](https://fal.ai/models/fal-ai/pixverse/swap/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/pixverse/swap)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
