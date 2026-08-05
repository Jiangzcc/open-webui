# sync.so -- lipsync 1.9.0-beta

> Generate realistic lipsync animations from audio using advanced algorithms for high-quality synchronization.


## Overview

- **Endpoint**: `https://fal.run/fal-ai/sync-lipsync`
- **Model ID**: `fal-ai/sync-lipsync`
- **Category**: video-to-video
- **Kind**: inference
**Tags**: animation, lip sync



## Pricing

- **Price**: $0.7 per minutes

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`model`** (`ModelEnum`, _optional_):
  The model to use for lipsyncing Default value: `"lipsync-1.9.0-beta"`
  - Default: `"lipsync-1.9.0-beta"`
  - Options: `"lipsync-1.8.0"`, `"lipsync-1.7.1"`, `"lipsync-1.9.0-beta"`

- **`video_url`** (`string`, _required_):
  URL of the input video
  - Examples: "https://fal.media/files/koala/8teUPbRRMtAUTORDvqy0l.mp4"

- **`audio_url`** (`string`, _required_):
  URL of the input audio
  - Examples: "https://fal.media/files/lion/vyFWygmZsIZlUO4s0nr2n.wav"

- **`sync_mode`** (`SyncModeEnum`, _optional_):
  Lipsync mode when audio and video durations are out of sync. Default value: `"cut_off"`
  - Default: `"cut_off"`
  - Options: `"cut_off"`, `"loop"`, `"bounce"`, `"silence"`, `"remap"`



**Required Parameters Example**:

```json
{
  "video_url": "https://fal.media/files/koala/8teUPbRRMtAUTORDvqy0l.mp4",
  "audio_url": "https://fal.media/files/lion/vyFWygmZsIZlUO4s0nr2n.wav"
}
```

**Full Example**:

```json
{
  "model": "lipsync-1.9.0-beta",
  "video_url": "https://fal.media/files/koala/8teUPbRRMtAUTORDvqy0l.mp4",
  "audio_url": "https://fal.media/files/lion/vyFWygmZsIZlUO4s0nr2n.wav",
  "sync_mode": "cut_off"
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`File`, _required_):
  The generated video
  - Examples: {"url":"https://v3.fal.media/files/rabbit/6gJV-z7RJsF0AxkZHkdgJ_output.mp4"}



**Example Response**:

```json
{
  "video": {
    "url": "https://v3.fal.media/files/rabbit/6gJV-z7RJsF0AxkZHkdgJ_output.mp4"
  }
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/sync-lipsync \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "video_url": "https://fal.media/files/koala/8teUPbRRMtAUTORDvqy0l.mp4",
     "audio_url": "https://fal.media/files/lion/vyFWygmZsIZlUO4s0nr2n.wav"
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
    "fal-ai/sync-lipsync",
    arguments={
        "video_url": "https://fal.media/files/koala/8teUPbRRMtAUTORDvqy0l.mp4",
        "audio_url": "https://fal.media/files/lion/vyFWygmZsIZlUO4s0nr2n.wav"
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

const result = await fal.subscribe("fal-ai/sync-lipsync", {
  input: {
    video_url: "https://fal.media/files/koala/8teUPbRRMtAUTORDvqy0l.mp4",
    audio_url: "https://fal.media/files/lion/vyFWygmZsIZlUO4s0nr2n.wav"
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

- [Model Playground](https://fal.ai/models/fal-ai/sync-lipsync)
- [API Documentation](https://fal.ai/models/fal-ai/sync-lipsync/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/sync-lipsync)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
