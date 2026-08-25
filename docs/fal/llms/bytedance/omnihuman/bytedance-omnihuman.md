# OmniHuman

> OmniHuman generates video using an image of a human figure paired with an audio file. It produces vivid, high-quality videos where the character’s emotions and movements maintain a strong correlation with the audio.


## Overview

- **Endpoint**: `https://fal.run/fal-ai/bytedance/omnihuman`
- **Model ID**: `fal-ai/bytedance/omnihuman`
- **Category**: image-to-video
- **Kind**: inference
**Tags**: image-to-video, lipsync



## Pricing

- **Price**: $0.14 per seconds

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`image_url`** (`string`, _required_):
  The URL of the image used to generate the video
  - Examples: "https://storage.googleapis.com/falserverless/example_inputs/omnihuman.png"

- **`audio_url`** (`string`, _required_):
  The URL of the audio file to generate the video. Audio must be under 30s long.
  - Examples: "https://storage.googleapis.com/falserverless/example_inputs/omnihuman_audio.mp3"



**Required Parameters Example**:

```json
{
  "image_url": "https://storage.googleapis.com/falserverless/example_inputs/omnihuman.png",
  "audio_url": "https://storage.googleapis.com/falserverless/example_inputs/omnihuman_audio.mp3"
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`File`, _required_):
  Generated video file
  - Examples: {"url":"https://storage.googleapis.com/falserverless/example_outputs/omnihuman_output.mp4"}

- **`duration`** (`float`, _required_):
  Duration of audio input/video output as used for billing.



**Example Response**:

```json
{
  "video": {
    "url": "https://storage.googleapis.com/falserverless/example_outputs/omnihuman_output.mp4"
  }
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/bytedance/omnihuman \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "image_url": "https://storage.googleapis.com/falserverless/example_inputs/omnihuman.png",
     "audio_url": "https://storage.googleapis.com/falserverless/example_inputs/omnihuman_audio.mp3"
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
    "fal-ai/bytedance/omnihuman",
    arguments={
        "image_url": "https://storage.googleapis.com/falserverless/example_inputs/omnihuman.png",
        "audio_url": "https://storage.googleapis.com/falserverless/example_inputs/omnihuman_audio.mp3"
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

const result = await fal.subscribe("fal-ai/bytedance/omnihuman", {
  input: {
    image_url: "https://storage.googleapis.com/falserverless/example_inputs/omnihuman.png",
    audio_url: "https://storage.googleapis.com/falserverless/example_inputs/omnihuman_audio.mp3"
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

- [Model Playground](https://fal.ai/models/fal-ai/bytedance/omnihuman)
- [API Documentation](https://fal.ai/models/fal-ai/bytedance/omnihuman/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/bytedance/omnihuman)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
