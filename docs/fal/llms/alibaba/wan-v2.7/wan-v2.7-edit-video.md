# Wan

> Wan 2.7 is the latest generation AI video model, delivering enhanced motion smoothness, superior scene fidelity, and greater visual coherence.


## Overview

- **Endpoint**: `https://fal.run/fal-ai/wan/v2.7/edit-video`
- **Model ID**: `fal-ai/wan/v2.7/edit-video`
- **Category**: video-to-video
- **Kind**: inference
**Tags**: stylized, transform, lipsync



## Pricing

- **Price**: $0.1 per seconds

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _required_):
  Editing instruction or style transfer description.
  - Examples: "Transform the entire scene into a beautiful watercolor painting style. Soft brushstrokes, flowing paint washes, visible paper texture. Colors should bleed and blend naturally like wet watercolor on paper."

- **`video_url`** (`string`, _required_):
  URL of the input video to edit. Format: MP4, MOV. Duration: 2-10s. Max 100 MB.
  
  Max file size: 100.0MB, Min duration: 2s, Max duration: 10s, Timeout: 30.0s
  - Examples: "https://v3b.fal.media/files/b/0a940a70/s4jC3lmmbU8Q6xM-SFtWB_m5JJudvy.mp4"

- **`reference_image_url`** (`string`, _optional_):
  Reference image URL for reference-based editing.

- **`resolution`** (`ResolutionEnum`, _optional_):
  Output video resolution tier. Default value: `"1080p"`
  - Default: `"1080p"`
  - Options: `"720p"`, `"1080p"`

- **`aspect_ratio`** (`Enum`, _optional_):
  Aspect ratio of the generated video. If not provided, uses the aspect ratio of the input video.
  - Options: `"16:9"`, `"9:16"`, `"1:1"`, `"4:3"`, `"3:4"`

- **`duration`** (`DurationEnum`, _optional_):
  Output video duration in seconds. Default 0 means match input video duration. When set (2-10), truncates from the start. Default value: `"0"`
  - Default: `0`
  - Options: `0`, `2`, `3`, `4`, `5`, `6`, `7`, `8`, `9`, `10`

- **`audio_setting`** (`AudioSettingEnum`, _optional_):
  Audio handling. 'auto': model decides whether to regenerate audio. 'origin': preserve original audio from input video. Default value: `"auto"`
  - Default: `"auto"`
  - Options: `"auto"`, `"origin"`

- **`seed`** (`integer`, _optional_):
  Random seed for reproducibility (0-2147483647).

- **`enable_safety_checker`** (`boolean`, _optional_):
  Enable content moderation for input and output. Default value: `true`
  - Default: `true`



**Required Parameters Example**:

```json
{
  "prompt": "Transform the entire scene into a beautiful watercolor painting style. Soft brushstrokes, flowing paint washes, visible paper texture. Colors should bleed and blend naturally like wet watercolor on paper.",
  "video_url": "https://v3b.fal.media/files/b/0a940a70/s4jC3lmmbU8Q6xM-SFtWB_m5JJudvy.mp4"
}
```

**Full Example**:

```json
{
  "prompt": "Transform the entire scene into a beautiful watercolor painting style. Soft brushstrokes, flowing paint washes, visible paper texture. Colors should bleed and blend naturally like wet watercolor on paper.",
  "video_url": "https://v3b.fal.media/files/b/0a940a70/s4jC3lmmbU8Q6xM-SFtWB_m5JJudvy.mp4",
  "resolution": "1080p",
  "audio_setting": "auto",
  "enable_safety_checker": true
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`VideoFile`, _required_):
  The edited video file.

- **`seed`** (`integer`, _required_):
  The seed used for generation.

- **`actual_prompt`** (`string`, _optional_):
  The actual prompt used if prompt rewriting was enabled.



**Example Response**:

```json
{
  "video": {
    "url": "",
    "content_type": "image/png",
    "file_name": "z9RV14K95DvU.png",
    "file_size": 4404019
  }
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/wan/v2.7/edit-video \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "Transform the entire scene into a beautiful watercolor painting style. Soft brushstrokes, flowing paint washes, visible paper texture. Colors should bleed and blend naturally like wet watercolor on paper.",
     "video_url": "https://v3b.fal.media/files/b/0a940a70/s4jC3lmmbU8Q6xM-SFtWB_m5JJudvy.mp4"
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
    "fal-ai/wan/v2.7/edit-video",
    arguments={
        "prompt": "Transform the entire scene into a beautiful watercolor painting style. Soft brushstrokes, flowing paint washes, visible paper texture. Colors should bleed and blend naturally like wet watercolor on paper.",
        "video_url": "https://v3b.fal.media/files/b/0a940a70/s4jC3lmmbU8Q6xM-SFtWB_m5JJudvy.mp4"
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

const result = await fal.subscribe("fal-ai/wan/v2.7/edit-video", {
  input: {
    prompt: "Transform the entire scene into a beautiful watercolor painting style. Soft brushstrokes, flowing paint washes, visible paper texture. Colors should bleed and blend naturally like wet watercolor on paper.",
    video_url: "https://v3b.fal.media/files/b/0a940a70/s4jC3lmmbU8Q6xM-SFtWB_m5JJudvy.mp4"
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

- [Model Playground](https://fal.ai/models/fal-ai/wan/v2.7/edit-video)
- [API Documentation](https://fal.ai/models/fal-ai/wan/v2.7/edit-video/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/wan/v2.7/edit-video)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
