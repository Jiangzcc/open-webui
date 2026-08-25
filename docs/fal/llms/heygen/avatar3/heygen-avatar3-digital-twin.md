# Heygen

> Heygen Avatar V3 Model for Digital Twin


## Overview

- **Endpoint**: `https://fal.run/fal-ai/heygen/avatar3/digital-twin`
- **Model ID**: `fal-ai/heygen/avatar3/digital-twin`
- **Category**: text-to-video
- **Kind**: inference
**Tags**: text-to-video



## Pricing

Your request will cost **$0.034** per output video second.

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`character`** (`Character`, _required_):
  Character configuration for the video

- **`voice`** (`TextVoice`, _required_):
  Voice configuration for the character

- **`audio_url`** (`string`, _optional_):
  URL of an audio file for the avatar to lip-sync to. When provided, the avatar uses this audio instead of text-to-speech.

- **`resolution`** (`ResolutionEnum`, _optional_):
  Video resolution preset. Options: 360p, 480p, 540p, 720p, 1080p Default value: `"720p"`
  - Default: `"720p"`
  - Options: `"360p"`, `"480p"`, `"540p"`, `"720p"`, `"1080p"`

- **`aspect_ratio`** (`AspectRatioEnum`, _optional_):
  Aspect ratio of the output video. Use '9:16' for portrait (vertical) videos, '16:9' for landscape, '1:1' for square, '4:5' for portrait social video, or '5:4' for landscape social video. Default value: `"16:9"`
  - Default: `"16:9"`
  - Options: `"16:9"`, `"9:16"`, `"4:5"`, `"5:4"`, `"1:1"`



**Required Parameters Example**:

```json
{
  "character": {
    "avatar": "Florin Business Sitting Side"
  },
  "voice": {}
}
```

**Full Example**:

```json
{
  "character": {
    "avatar": "Florin Business Sitting Side",
    "avatar_style": "closeUp"
  },
  "voice": {
    "prompt": "The Tesla Cybertruck is a battery-electric full-size pickup truck manufactured by Tesla, Inc. since 2023.",
    "voice": "Charming Charlie - Excited 🤩",
    "speed": 1
  },
  "resolution": "720p",
  "aspect_ratio": "16:9"
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`File`, _required_):
  The generated video file
  - Examples: {"url":"https://v3b.fal.media/files/b/0a8f61f5/SwAbhEQ0tNLthNkyTqCRn_translated.mp4"}



**Example Response**:

```json
{
  "video": {
    "url": "https://v3b.fal.media/files/b/0a8f61f5/SwAbhEQ0tNLthNkyTqCRn_translated.mp4"
  }
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/heygen/avatar3/digital-twin \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "character": {
       "avatar": "Florin Business Sitting Side"
     },
     "voice": {}
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
    "fal-ai/heygen/avatar3/digital-twin",
    arguments={
        "character": {
            "avatar": "Florin Business Sitting Side"
        },
        "voice": {}
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

const result = await fal.subscribe("fal-ai/heygen/avatar3/digital-twin", {
  input: {
    character: {
      avatar: "Florin Business Sitting Side"
    },
    voice: {}
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

- [Model Playground](https://fal.ai/models/fal-ai/heygen/avatar3/digital-twin)
- [API Documentation](https://fal.ai/models/fal-ai/heygen/avatar3/digital-twin/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/heygen/avatar3/digital-twin)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
