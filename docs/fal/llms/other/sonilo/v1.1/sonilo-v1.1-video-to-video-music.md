# V1.1 Video to Video Music

> Generates perfectly synced music for any video. Return a licensed music soundtrack ready for commercial use (optional preservation of the original speech in video)


## Overview

- **Endpoint**: `https://fal.run/sonilo/v1.1/video-to-video-music`
- **Model ID**: `sonilo/v1.1/video-to-video-music`
- **Category**: video-to-video
- **Kind**: inference
**Tags**: music, editing, restoration



## Pricing

Your request will cost **$0.009** per second of output and per sample.

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`video_url`** (`string`, _required_):
  Public http(s) URL of the source video to score.
  - Examples: "https://v3b.fal.media/files/b/0a9ddd00/2QssaYyFxstvVlmIraSns_Sonilo_Demo_Original_1.mp4"

- **`keep_speech_vocal`** (`boolean`, _optional_):
  Keep the original video's speech/vocals. When on, the source audio is separated (music source separation), and only the isolated vocals are blended over the generated music with automatic ducking (the music dips under speech). When off (default), the original soundtrack is dropped and the video carries only the generated music.
  - Default: `false`

- **`num_samples`** (`integer`, _optional_):
  How many distinct scored videos to generate. Default value: `1`
  - Default: `1`
  - Range: `1` to `3`

- **`prompt`** (`string`, _optional_):
  Optional text prompt steering the musical style. If omitted, a prompt is generated automatically from the video.

- **`prompt_influence`** (`float`, _optional_):
  Turn it up to match the text prompt Default value: `0.5`
  - Default: `0.5`
  - Range: `0` to `1`

- **`start_offset`** (`float`, _optional_):
  Optional. Start scoring from this offset (seconds) into the video. Requires Start Offset + Duration <= Video Duration.
  - Range: `0` to `600`

- **`duration`** (`float`, _optional_):
  Optional. Length (seconds) of the video segment to score. When set, scores a segment of this length starting at Start Offset (or from the beginning if Start Offset is unset). Defaults (None) to the rest of the video.
  - Range: `1` to `600`



**Required Parameters Example**:

```json
{
  "video_url": "https://v3b.fal.media/files/b/0a9ddd00/2QssaYyFxstvVlmIraSns_Sonilo_Demo_Original_1.mp4"
}
```

**Full Example**:

```json
{
  "video_url": "https://v3b.fal.media/files/b/0a9ddd00/2QssaYyFxstvVlmIraSns_Sonilo_Demo_Original_1.mp4",
  "num_samples": 1,
  "prompt_influence": 0.5
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`Video`, _required_):
  The first scored video (source video muxed with generated music).

- **`videos`** (`list<Video>`, _required_):
  All scored videos (mp4), one per sample.
  - Array of Video



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
  ]
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/sonilo/v1.1/video-to-video-music \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "video_url": "https://v3b.fal.media/files/b/0a9ddd00/2QssaYyFxstvVlmIraSns_Sonilo_Demo_Original_1.mp4"
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
    "sonilo/v1.1/video-to-video-music",
    arguments={
        "video_url": "https://v3b.fal.media/files/b/0a9ddd00/2QssaYyFxstvVlmIraSns_Sonilo_Demo_Original_1.mp4"
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

const result = await fal.subscribe("sonilo/v1.1/video-to-video-music", {
  input: {
    video_url: "https://v3b.fal.media/files/b/0a9ddd00/2QssaYyFxstvVlmIraSns_Sonilo_Demo_Original_1.mp4"
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

- [Model Playground](https://fal.ai/models/sonilo/v1.1/video-to-video-music)
- [API Documentation](https://fal.ai/models/sonilo/v1.1/video-to-video-music/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=sonilo/v1.1/video-to-video-music)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
