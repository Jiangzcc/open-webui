# Heygen

> Heygen Photo Avatar 4 Model


## Overview

- **Endpoint**: `https://fal.run/fal-ai/heygen/avatar4/image-to-video`
- **Model ID**: `fal-ai/heygen/avatar4/image-to-video`
- **Category**: image-to-video
- **Kind**: inference
**Tags**: image-to-video



## Pricing

Your request will cost **$0.1** per output video second.

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`image_url`** (`string`, _required_):
  URL of the image to animate. The image should contain a clear face.
  - Examples: "https://v3b.fal.media/files/b/0a90062c/A7EIviZqNxZ2HAs0yHeZ6_77a05b99-8588-4ffc-90aa-be7f9d34e9d3.png"

- **`prompt`** (`string`, _optional_):
  The text the avatar will speak
  - Examples: "Hey friends! Welcome to the GPU force podcast and today we are going to discuss about the rising GPU cost!"

- **`voice`** (`string`, _optional_):
  Name of the voice to use for the avatar
  - Examples: "Melissa"

- **`audio_url`** (`string`, _optional_):
  URL of an audio file for the avatar to lip-sync to. When provided, overrides prompt and voice.

- **`talking_style`** (`TalkingStyleEnum`, _optional_):
  Talking style - 'stable' for minimal movement, 'expressive' for more animation Default value: `"stable"`
  - Default: `"stable"`
  - Options: `"stable"`, `"expressive"`

- **`expression`** (`string`, _optional_):
  Facial expression

- **`background`** (`AvatarIVBackground`, _optional_):
  Background configuration

- **`resolution`** (`ResolutionEnum`, _optional_):
  Video resolution preset. Options: 360p, 480p, 540p, 720p, 1080p Default value: `"720p"`
  - Default: `"720p"`
  - Options: `"360p"`, `"480p"`, `"540p"`, `"720p"`, `"1080p"`

- **`aspect_ratio`** (`AspectRatioEnum`, _optional_):
  Aspect ratio of the output video. Supported values: '16:9', '9:16', '4:5', '5:4', '1:1', and 'auto'. 'auto' preserves the source aspect ratio when HeyGen can read it, falling back to '16:9' otherwise. Default value: `"16:9"`
  - Default: `"16:9"`
  - Options: `"16:9"`, `"9:16"`, `"4:5"`, `"5:4"`, `"1:1"`, `"auto"`

- **`caption`** (`boolean`, _optional_):
  Whether to add captions to the video
  - Default: `false`



**Required Parameters Example**:

```json
{
  "image_url": "https://v3b.fal.media/files/b/0a90062c/A7EIviZqNxZ2HAs0yHeZ6_77a05b99-8588-4ffc-90aa-be7f9d34e9d3.png"
}
```

**Full Example**:

```json
{
  "image_url": "https://v3b.fal.media/files/b/0a90062c/A7EIviZqNxZ2HAs0yHeZ6_77a05b99-8588-4ffc-90aa-be7f9d34e9d3.png",
  "prompt": "Hey friends! Welcome to the GPU force podcast and today we are going to discuss about the rising GPU cost!",
  "voice": "Melissa",
  "talking_style": "stable",
  "resolution": "720p",
  "aspect_ratio": "16:9"
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`File`, _required_):
  The generated video file
  - Examples: {"content_type":"video/mp4","file_name":"output.mp4","file_size":2466524,"url":"https://v3b.fal.media/files/b/0a900636/DUES0_z4i7FWnife02ieH_output.mp4"}



**Example Response**:

```json
{
  "video": {
    "content_type": "video/mp4",
    "file_name": "output.mp4",
    "file_size": 2466524,
    "url": "https://v3b.fal.media/files/b/0a900636/DUES0_z4i7FWnife02ieH_output.mp4"
  }
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/heygen/avatar4/image-to-video \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "image_url": "https://v3b.fal.media/files/b/0a90062c/A7EIviZqNxZ2HAs0yHeZ6_77a05b99-8588-4ffc-90aa-be7f9d34e9d3.png"
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
    "fal-ai/heygen/avatar4/image-to-video",
    arguments={
        "image_url": "https://v3b.fal.media/files/b/0a90062c/A7EIviZqNxZ2HAs0yHeZ6_77a05b99-8588-4ffc-90aa-be7f9d34e9d3.png"
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

const result = await fal.subscribe("fal-ai/heygen/avatar4/image-to-video", {
  input: {
    image_url: "https://v3b.fal.media/files/b/0a90062c/A7EIviZqNxZ2HAs0yHeZ6_77a05b99-8588-4ffc-90aa-be7f9d34e9d3.png"
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

- [Model Playground](https://fal.ai/models/fal-ai/heygen/avatar4/image-to-video)
- [API Documentation](https://fal.ai/models/fal-ai/heygen/avatar4/image-to-video/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/heygen/avatar4/image-to-video)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
