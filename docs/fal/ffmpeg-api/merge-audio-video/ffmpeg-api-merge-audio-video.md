# Ffmpeg Api Merge Audio-Video

> Merge videos with standalone audio files or audio from video files.


## Overview

- **Endpoint**: `https://fal.run/fal-ai/ffmpeg-api/merge-audio-video`
- **Model ID**: `fal-ai/ffmpeg-api/merge-audio-video`
- **Category**: video-to-video
- **Kind**: inference
**Tags**: ffmpeg



## Pricing

- **Price**: $0.0002 per seconds

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`video_url`** (`string`, _required_):
  URL of the video file to use as the video track
  - Examples: "https://storage.googleapis.com/falserverless/example_inputs/ffmpeg-video.mp4"

- **`audio_url`** (`string`, _required_):
  URL of the audio file to use as the audio track
  - Examples: "https://storage.googleapis.com/falserverless/example_inputs/ffmpeg-audio.wav"

- **`start_offset`** (`float`, _optional_):
  Offset in seconds for when the audio should start relative to the video
  - Default: `0`



**Required Parameters Example**:

```json
{
  "video_url": "https://storage.googleapis.com/falserverless/example_inputs/ffmpeg-video.mp4",
  "audio_url": "https://storage.googleapis.com/falserverless/example_inputs/ffmpeg-audio.wav"
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`File`, _required_):
  Output video with merged audio.



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
  --url https://fal.run/fal-ai/ffmpeg-api/merge-audio-video \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "video_url": "https://storage.googleapis.com/falserverless/example_inputs/ffmpeg-video.mp4",
     "audio_url": "https://storage.googleapis.com/falserverless/example_inputs/ffmpeg-audio.wav"
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
    "fal-ai/ffmpeg-api/merge-audio-video",
    arguments={
        "video_url": "https://storage.googleapis.com/falserverless/example_inputs/ffmpeg-video.mp4",
        "audio_url": "https://storage.googleapis.com/falserverless/example_inputs/ffmpeg-audio.wav"
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

const result = await fal.subscribe("fal-ai/ffmpeg-api/merge-audio-video", {
  input: {
    video_url: "https://storage.googleapis.com/falserverless/example_inputs/ffmpeg-video.mp4",
    audio_url: "https://storage.googleapis.com/falserverless/example_inputs/ffmpeg-audio.wav"
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

- [Model Playground](https://fal.ai/models/fal-ai/ffmpeg-api/merge-audio-video)
- [API Documentation](https://fal.ai/models/fal-ai/ffmpeg-api/merge-audio-video/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/ffmpeg-api/merge-audio-video)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
