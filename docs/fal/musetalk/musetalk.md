# MuseTalk

> MuseTalk is a real-time high quality audio-driven lip-syncing model. Use MuseTalk to animate a face with your own audio.


## Overview

- **Endpoint**: `https://fal.run/fal-ai/musetalk`
- **Model ID**: `fal-ai/musetalk`
- **Category**: image-to-video
- **Kind**: inference
**Tags**: animation, lip sync, real-time



## Pricing

- **Price**: $0 per compute seconds

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`source_video_url`** (`string`, _required_):
  URL of the source video
  - Examples: "https://raw.githubusercontent.com/TMElyralab/MuseTalk/main/data/video/sun.mp4"

- **`audio_url`** (`string`, _required_):
  URL of the audio
  - Examples: "https://raw.githubusercontent.com/TMElyralab/MuseTalk/main/data/audio/sun.wav"



**Required Parameters Example**:

```json
{
  "source_video_url": "https://raw.githubusercontent.com/TMElyralab/MuseTalk/main/data/video/sun.mp4",
  "audio_url": "https://raw.githubusercontent.com/TMElyralab/MuseTalk/main/data/audio/sun.wav"
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`File`, _required_):
  The generated video file.



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
  --url https://fal.run/fal-ai/musetalk \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "source_video_url": "https://raw.githubusercontent.com/TMElyralab/MuseTalk/main/data/video/sun.mp4",
     "audio_url": "https://raw.githubusercontent.com/TMElyralab/MuseTalk/main/data/audio/sun.wav"
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
    "fal-ai/musetalk",
    arguments={
        "source_video_url": "https://raw.githubusercontent.com/TMElyralab/MuseTalk/main/data/video/sun.mp4",
        "audio_url": "https://raw.githubusercontent.com/TMElyralab/MuseTalk/main/data/audio/sun.wav"
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

const result = await fal.subscribe("fal-ai/musetalk", {
  input: {
    source_video_url: "https://raw.githubusercontent.com/TMElyralab/MuseTalk/main/data/video/sun.mp4",
    audio_url: "https://raw.githubusercontent.com/TMElyralab/MuseTalk/main/data/audio/sun.wav"
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

- [Model Playground](https://fal.ai/models/fal-ai/musetalk)
- [API Documentation](https://fal.ai/models/fal-ai/musetalk/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/musetalk)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
