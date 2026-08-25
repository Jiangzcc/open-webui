# Happy Horse Video Edit

> HappyHorse video editing supports advanced video editing through natural language instructions. It allows for local or global editing of video elements using up to 5 reference images.


## Overview

- **Endpoint**: `https://fal.run/alibaba/happy-horse/video-edit`
- **Model ID**: `alibaba/happy-horse/video-edit`
- **Category**: video-to-video
- **Kind**: inference
**Tags**: happy-horse, video-editing, video-to-video



## Pricing

For every second of 720p video you generated, you will be charged **$0.28/second** (**$0.14**  per input second and **0.14** per output second).  For 1080p video you will be charged **$0.56/second**.

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`video_url`** (`string`, _required_):
  URL of the source video to edit. Formats: MP4, MOV (H.264 recommended). Duration: 3-60 s. Longer side ≤ 2160 px, shorter side ≥ 320 px. Aspect ratio between 1:2.5 and 2.5:1. Frame rate > 8 fps. Max 100 MB. The output video preserves the source aspect ratio. Output duration matches the input video, capped at 15 s (longer inputs are truncated to the first 15 s).
  
  Max file size: 100.0MB, Min duration: 3s, Max duration: 60s, Timeout: 30.0s
  - Examples: "https://v3b.fal.media/files/b/0a8675cf/bCu9FiFXSjsSnIwOmjUOY_BVs2IFR3.mp4"

- **`prompt`** (`string`, _required_):
  Text prompt describing the desired edit. Reference any supplied reference images using @Image1, @Image2, ... up to @Image5. Max 2500 characters.
  - Examples: "Recolor the sky to a deep purple sunset."

- **`reference_image_urls`** (`list<string>`, _optional_):
  Optional reference images used to guide the edit (up to 5). Formats: JPEG, JPG, PNG, WEBP. Dimensions must be at least 300px. Aspect ratio between 1:2.5 and 2.5:1. Max 10 MB each.
  - Array of string

- **`resolution`** (`ResolutionEnum`, _optional_):
  Output video resolution tier. Default value: `"1080p"`
  - Default: `"1080p"`
  - Options: `"720p"`, `"1080p"`

- **`audio_setting`** (`AudioSettingEnum`, _optional_):
  Audio handling. 'auto': model decides whether to regenerate audio. 'origin': preserve the original audio from the input video. Default value: `"auto"`
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
  "video_url": "https://v3b.fal.media/files/b/0a8675cf/bCu9FiFXSjsSnIwOmjUOY_BVs2IFR3.mp4",
  "prompt": "Recolor the sky to a deep purple sunset."
}
```

**Full Example**:

```json
{
  "video_url": "https://v3b.fal.media/files/b/0a8675cf/bCu9FiFXSjsSnIwOmjUOY_BVs2IFR3.mp4",
  "prompt": "Recolor the sky to a deep purple sunset.",
  "resolution": "1080p",
  "audio_setting": "auto",
  "enable_safety_checker": true
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`VideoFile`, _required_):
  The generated video file.

- **`seed`** (`integer`, _required_):
  The seed used for generation.



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
  --url https://fal.run/alibaba/happy-horse/video-edit \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "video_url": "https://v3b.fal.media/files/b/0a8675cf/bCu9FiFXSjsSnIwOmjUOY_BVs2IFR3.mp4",
     "prompt": "Recolor the sky to a deep purple sunset."
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
    "alibaba/happy-horse/video-edit",
    arguments={
        "video_url": "https://v3b.fal.media/files/b/0a8675cf/bCu9FiFXSjsSnIwOmjUOY_BVs2IFR3.mp4",
        "prompt": "Recolor the sky to a deep purple sunset."
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

const result = await fal.subscribe("alibaba/happy-horse/video-edit", {
  input: {
    video_url: "https://v3b.fal.media/files/b/0a8675cf/bCu9FiFXSjsSnIwOmjUOY_BVs2IFR3.mp4",
    prompt: "Recolor the sky to a deep purple sunset."
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

- [Model Playground](https://fal.ai/models/alibaba/happy-horse/video-edit)
- [API Documentation](https://fal.ai/models/alibaba/happy-horse/video-edit/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=alibaba/happy-horse/video-edit)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
