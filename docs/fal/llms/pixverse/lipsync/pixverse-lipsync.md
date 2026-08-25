# PixVerse Lipsync

> Generate realistic lipsync animations from audio using advanced algorithms for high-quality synchronization with PixVerse Lipsync model


## Overview

- **Endpoint**: `https://fal.run/fal-ai/pixverse/lipsync`
- **Model ID**: `fal-ai/pixverse/lipsync`
- **Category**: video-to-video
- **Kind**: inference
**Tags**: animation, lip sync



## Pricing

For every second of output videos your request will cost **$0.04**. If audio is not provided for every 100 characters your request will cost **$0.24**.

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`video_url`** (`string`, _required_):
  URL of the input video
  - Examples: "https://v3.fal.media/files/penguin/T-ONORYMYLoEOB9lXryA2_IKEy3yAyi1evJGBAkXGZx_output.mp4"

- **`audio_url`** (`string`, _optional_):
  URL of the input audio. If not provided, TTS will be used.
  - Examples: "https://v3.fal.media/files/monkey/k4iyN8bJZWwJXMKH-pO9r_speech.mp3"

- **`voice_id`** (`VoiceIdEnum`, _optional_):
  Voice to use for TTS when audio_url is not provided Default value: `"Auto"`
  - Default: `"Auto"`
  - Options: `"Emily"`, `"James"`, `"Isabella"`, `"Liam"`, `"Chloe"`, `"Adrian"`, `"Harper"`, `"Ava"`, `"Sophia"`, `"Julia"`, `"Mason"`, `"Jack"`, `"Oliver"`, `"Ethan"`, `"Auto"`

- **`text`** (`string`, _optional_):
  Text content for TTS when audio_url is not provided
  - Examples: "Hello, this is a test message."



**Required Parameters Example**:

```json
{
  "video_url": "https://v3.fal.media/files/penguin/T-ONORYMYLoEOB9lXryA2_IKEy3yAyi1evJGBAkXGZx_output.mp4"
}
```

**Full Example**:

```json
{
  "video_url": "https://v3.fal.media/files/penguin/T-ONORYMYLoEOB9lXryA2_IKEy3yAyi1evJGBAkXGZx_output.mp4",
  "audio_url": "https://v3.fal.media/files/monkey/k4iyN8bJZWwJXMKH-pO9r_speech.mp3",
  "voice_id": "Auto",
  "text": "Hello, this is a test message."
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`File`, _required_):
  The generated video
  - Examples: {"file_size":1732359,"file_name":"output.mp4","content_type":"video/mp4","url":"https://v3.fal.media/files/penguin/hsR_KXBJjuF3IIVYIIDA2_output.mp4"}



**Example Response**:

```json
{
  "video": {
    "file_size": 1732359,
    "file_name": "output.mp4",
    "content_type": "video/mp4",
    "url": "https://v3.fal.media/files/penguin/hsR_KXBJjuF3IIVYIIDA2_output.mp4"
  }
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/pixverse/lipsync \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "video_url": "https://v3.fal.media/files/penguin/T-ONORYMYLoEOB9lXryA2_IKEy3yAyi1evJGBAkXGZx_output.mp4"
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
    "fal-ai/pixverse/lipsync",
    arguments={
        "video_url": "https://v3.fal.media/files/penguin/T-ONORYMYLoEOB9lXryA2_IKEy3yAyi1evJGBAkXGZx_output.mp4"
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

const result = await fal.subscribe("fal-ai/pixverse/lipsync", {
  input: {
    video_url: "https://v3.fal.media/files/penguin/T-ONORYMYLoEOB9lXryA2_IKEy3yAyi1evJGBAkXGZx_output.mp4"
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

- [Model Playground](https://fal.ai/models/fal-ai/pixverse/lipsync)
- [API Documentation](https://fal.ai/models/fal-ai/pixverse/lipsync/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/pixverse/lipsync)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
