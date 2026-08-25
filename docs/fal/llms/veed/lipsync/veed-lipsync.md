# Lipsync

> Generate realistic lipsync from any audio using VEED's model.


## Overview

- **Endpoint**: `https://fal.run/veed/lipsync`
- **Model ID**: `veed/lipsync`
- **Category**: video-to-video
- **Kind**: inference
**Tags**: lipsync, video-to-video, avatar



## Pricing

- **Price**: $0.4 per minutes

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`video_url`** (`string`, _required_)
  - Examples: "https://v3.fal.media/files/monkey/q1fDPhrpfjfsaRmbhTed4_influencer.mp4"

- **`audio_url`** (`string`, _required_)
  - Examples: "https://v3.fal.media/files/rabbit/Ql3ade3wEKlZXRQLRbhxm_tts.mp3"



**Required Parameters Example**:

```json
{
  "video_url": "https://v3.fal.media/files/monkey/q1fDPhrpfjfsaRmbhTed4_influencer.mp4",
  "audio_url": "https://v3.fal.media/files/rabbit/Ql3ade3wEKlZXRQLRbhxm_tts.mp3"
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`File`, _required_)
  - Examples: {"content_type":"video/mp4","url":"https://v3.fal.media/files/penguin/PsA4BJPGAojXKW2QGztm4_tmpe_e1cgbq.mp4"}



**Example Response**:

```json
{
  "video": {
    "content_type": "video/mp4",
    "url": "https://v3.fal.media/files/penguin/PsA4BJPGAojXKW2QGztm4_tmpe_e1cgbq.mp4"
  }
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/veed/lipsync \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "video_url": "https://v3.fal.media/files/monkey/q1fDPhrpfjfsaRmbhTed4_influencer.mp4",
     "audio_url": "https://v3.fal.media/files/rabbit/Ql3ade3wEKlZXRQLRbhxm_tts.mp3"
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
    "veed/lipsync",
    arguments={
        "video_url": "https://v3.fal.media/files/monkey/q1fDPhrpfjfsaRmbhTed4_influencer.mp4",
        "audio_url": "https://v3.fal.media/files/rabbit/Ql3ade3wEKlZXRQLRbhxm_tts.mp3"
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

const result = await fal.subscribe("veed/lipsync", {
  input: {
    video_url: "https://v3.fal.media/files/monkey/q1fDPhrpfjfsaRmbhTed4_influencer.mp4",
    audio_url: "https://v3.fal.media/files/rabbit/Ql3ade3wEKlZXRQLRbhxm_tts.mp3"
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

- [Model Playground](https://fal.ai/models/veed/lipsync)
- [API Documentation](https://fal.ai/models/veed/lipsync/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=veed/lipsync)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
