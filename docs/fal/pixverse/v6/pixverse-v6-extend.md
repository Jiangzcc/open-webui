# PixVerse V6 Extend

> Pixverse's latest v6 Model.


## Overview

- **Endpoint**: `https://fal.run/fal-ai/pixverse/v6/extend`
- **Model ID**: `fal-ai/pixverse/v6/extend`
- **Category**: video-to-video
- **Kind**: inference
**Tags**: video-to-video, extend



## Pricing

Billing is calculated per second of video generated. For 360p, your request will cost **$0.025** per second without audio and **$0.035** per second with audio. For 540p, it will cost **$0.035** per second without audio and **$0.045** per second with audio. For 720p, it will cost **$0.045** per second without audio and **$0.060** per second with audio. For 1080p, it will cost **$0.090** per second without audio and **$0.115** per second with audio. For **$1** you can run this model for approximately **40 seconds** at 360p (no audio) or about **11 seconds** at 1080p (no audio).

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`video_url`** (`string`, _required_):
  URL of the input video to extend
  - Examples: "https://v3.fal.media/files/rabbit/88-jI3VWXU4Q8kSNrWo3c_output.mp4"

- **`prompt`** (`string`, _required_):
  Prompt describing how to extend the video. Limited to 2048 UTF-8 encoded bytes. Because the limit counts bytes rather than characters, emoji and non-Latin or accented characters (which use multiple bytes each) can push a visually short prompt over the cap.
  - Examples: "A kid is talking into camera"

- **`negative_prompt`** (`string`, _optional_):
  Negative prompt to be used for the generation. Limited to 2048 UTF-8 encoded bytes. Because the limit counts bytes rather than characters, emoji and non-Latin or accented characters (which use multiple bytes each) can push a visually short prompt over the cap. Default value: `""`
  - Default: `""`

- **`style`** (`Enum`, _optional_):
  The style of the extended video
  - Options: `"anime"`, `"3d_animation"`, `"clay"`, `"comic"`, `"cyberpunk"`

- **`resolution`** (`ResolutionEnum`, _optional_):
  The resolution of the generated video Default value: `"720p"`
  - Default: `"720p"`
  - Options: `"360p"`, `"540p"`, `"720p"`, `"1080p"`

- **`duration`** (`integer`, _optional_):
  The duration of the generated video in seconds. v6 supports values from 1 to 15 seconds Default value: `5`
  - Default: `5`
  - Range: `1` to `15`

- **`seed`** (`integer`, _optional_):
  Random seed for generation

- **`generate_audio_switch`** (`boolean`, _optional_):
  Enable audio generation (BGM, SFX, dialogue).
  - Default: `false`



**Required Parameters Example**:

```json
{
  "video_url": "https://v3.fal.media/files/rabbit/88-jI3VWXU4Q8kSNrWo3c_output.mp4",
  "prompt": "A kid is talking into camera"
}
```

**Full Example**:

```json
{
  "video_url": "https://v3.fal.media/files/rabbit/88-jI3VWXU4Q8kSNrWo3c_output.mp4",
  "prompt": "A kid is talking into camera",
  "resolution": "720p",
  "duration": 5
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`File`, _required_):
  The extended video
  - Examples: {"file_size":1163040,"file_name":"output.mp4","content_type":"video/mp4","url":"https://v3.fal.media/files/rabbit/88-jI3VWXU4Q8kSNrWo3c_output.mp4"}



**Example Response**:

```json
{
  "video": {
    "file_size": 1163040,
    "file_name": "output.mp4",
    "content_type": "video/mp4",
    "url": "https://v3.fal.media/files/rabbit/88-jI3VWXU4Q8kSNrWo3c_output.mp4"
  }
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/pixverse/v6/extend \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "video_url": "https://v3.fal.media/files/rabbit/88-jI3VWXU4Q8kSNrWo3c_output.mp4",
     "prompt": "A kid is talking into camera"
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
    "fal-ai/pixverse/v6/extend",
    arguments={
        "video_url": "https://v3.fal.media/files/rabbit/88-jI3VWXU4Q8kSNrWo3c_output.mp4",
        "prompt": "A kid is talking into camera"
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

const result = await fal.subscribe("fal-ai/pixverse/v6/extend", {
  input: {
    video_url: "https://v3.fal.media/files/rabbit/88-jI3VWXU4Q8kSNrWo3c_output.mp4",
    prompt: "A kid is talking into camera"
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

- [Model Playground](https://fal.ai/models/fal-ai/pixverse/v6/extend)
- [API Documentation](https://fal.ai/models/fal-ai/pixverse/v6/extend/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/pixverse/v6/extend)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
