# V1.1 Video to Video Sound Effects

> Adds synchronized, royalty-free, commercial-use-safe sound effects to a video. Returns the finished video with the generated audio mixed in.


## Overview

- **Endpoint**: `https://fal.run/sonilo/v1.1/video-to-video-sound-effects`
- **Model ID**: `sonilo/v1.1/video-to-video-sound-effects`
- **Category**: video-to-video
- **Kind**: inference
**Tags**: sfx, audio, effects, 



## Pricing

Your request will cost **$0.009** per second of output and per sample.

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`video_url`** (`string`, _required_):
  The video to add sound to (public URL, or upload a file). The generated audio matches the video's length.
  - Examples: "https://storage.googleapis.com/falserverless/model_tests/video_models/mmaudio_input.mp4"

- **`prompt`** (`string`, _optional_):
  Optional. Describe the kind of sound you want; it steers the generated audio for every scene. Leave empty to caption the video automatically.

- **`segments`** (`list<SfxSegment>`, _optional_):
  Optional. Split the video into time ranges, each with its own sound description. Leave empty to split into scenes automatically.
  - Array of SfxSegment

- **`audio_format`** (`AudioFormatEnum`, _optional_):
  Format of the returned audio file: aac (default), mp3, wav, or flac. (The video with sound is always AAC.) Default value: `"aac"`
  - Default: `"aac"`
  - Options: `"wav"`, `"mp3"`, `"aac"`, `"flac"`



**Required Parameters Example**:

```json
{
  "video_url": "https://storage.googleapis.com/falserverless/model_tests/video_models/mmaudio_input.mp4"
}
```

**Full Example**:

```json
{
  "video_url": "https://storage.googleapis.com/falserverless/model_tests/video_models/mmaudio_input.mp4",
  "segments": [
    {}
  ],
  "audio_format": "aac"
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`Video`, _required_):
  The video with the generated sound added (mp4). If no source video was given, this is an audio-only mp4.

- **`videos`** (`list<Video>`, _required_):
  All result videos (mp4), one per sample.
  - Array of Video

- **`audio`** (`Audio`, _required_):
  The generated sound as a separate audio file.



**Example Response**:

```json
{
  "video": {
    "url": "",
    "content_type": "image/png",
    "file_name": "z9RV14K95DvU.png",
    "file_size": 4404019
  },
  "videos": [
    {
      "url": "",
      "content_type": "image/png",
      "file_name": "z9RV14K95DvU.png",
      "file_size": 4404019
    }
  ],
  "audio": {
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
  --url https://fal.run/sonilo/v1.1/video-to-video-sound-effects \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "video_url": "https://storage.googleapis.com/falserverless/model_tests/video_models/mmaudio_input.mp4"
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
    "sonilo/v1.1/video-to-video-sound-effects",
    arguments={
        "video_url": "https://storage.googleapis.com/falserverless/model_tests/video_models/mmaudio_input.mp4"
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

const result = await fal.subscribe("sonilo/v1.1/video-to-video-sound-effects", {
  input: {
    video_url: "https://storage.googleapis.com/falserverless/model_tests/video_models/mmaudio_input.mp4"
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

- [Model Playground](https://fal.ai/models/sonilo/v1.1/video-to-video-sound-effects)
- [API Documentation](https://fal.ai/models/sonilo/v1.1/video-to-video-sound-effects/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=sonilo/v1.1/video-to-video-sound-effects)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
