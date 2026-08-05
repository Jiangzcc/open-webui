# Flashhead

> SoulX-FlashHead is a unified 1.3B-parameter framework designed for high-fidelity, infinite-length, and real-time streaming portrait video generation.


## Overview

- **Endpoint**: `https://fal.run/fal-ai/flashhead`
- **Model ID**: `fal-ai/flashhead`
- **Category**: image-to-video
- **Kind**: inference
**Tags**: portrait, video, streaming, real-time, face-animation, talking-head



## Pricing

- **Price**: $0.005 per seconds

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`image_url`** (`string`, _required_):
  URL of the face reference image. Portrait recommended.
  - Examples: "https://v3.fal.media/files/koala/gmpc0QevDF9bBsL1EAYVF_1c637094161147559f0910a68275dc34.png"

- **`text`** (`string`, _required_):
  Text to speak. Converted to speech via ElevenLabs.
  - Examples: "Hello there! How are you doing today?"

- **`voice`** (`VoiceEnum`, _optional_):
  ElevenLabs voice name. Default value: `"Aria"`
  - Default: `"Aria"`
  - Options: `"Aria"`, `"Roger"`, `"Sarah"`, `"Laura"`, `"Charlie"`, `"George"`, `"Callum"`, `"River"`, `"Liam"`, `"Charlotte"`, `"Alice"`, `"Matilda"`, `"Will"`, `"Jessica"`, `"Eric"`, `"Chris"`, `"Brian"`, `"Daniel"`, `"Lily"`, `"Bill"`

- **`stability`** (`float`, _optional_):
  Voice stability (0-1). Default value: `0.5`
  - Default: `0.5`
  - Range: `0` to `1`

- **`seed`** (`integer`, _optional_):
  Random seed for reproducibility.



**Required Parameters Example**:

```json
{
  "image_url": "https://v3.fal.media/files/koala/gmpc0QevDF9bBsL1EAYVF_1c637094161147559f0910a68275dc34.png",
  "text": "Hello there! How are you doing today?"
}
```

**Full Example**:

```json
{
  "image_url": "https://v3.fal.media/files/koala/gmpc0QevDF9bBsL1EAYVF_1c637094161147559f0910a68275dc34.png",
  "text": "Hello there! How are you doing today?",
  "voice": "Aria",
  "stability": 0.5
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`File`, _required_):
  Generated lip-synced avatar video (512x512, 25 FPS).
  - Examples: {"url":"https://v3.fal.media/files/tiger/bU0aYBX1nBFPAQ6txkP-Y_flashhead.mp4"}

- **`seed`** (`integer`, _required_):
  The seed used for generation.

- **`duration`** (`float`, _required_):
  Video duration in seconds.

- **`timings`** (`Timings`, _optional_):
  Timing breakdown.



**Example Response**:

```json
{
  "video": {
    "url": "https://v3.fal.media/files/tiger/bU0aYBX1nBFPAQ6txkP-Y_flashhead.mp4"
  }
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/flashhead \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "image_url": "https://v3.fal.media/files/koala/gmpc0QevDF9bBsL1EAYVF_1c637094161147559f0910a68275dc34.png",
     "text": "Hello there! How are you doing today?"
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
    "fal-ai/flashhead",
    arguments={
        "image_url": "https://v3.fal.media/files/koala/gmpc0QevDF9bBsL1EAYVF_1c637094161147559f0910a68275dc34.png",
        "text": "Hello there! How are you doing today?"
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

const result = await fal.subscribe("fal-ai/flashhead", {
  input: {
    image_url: "https://v3.fal.media/files/koala/gmpc0QevDF9bBsL1EAYVF_1c637094161147559f0910a68275dc34.png",
    text: "Hello there! How are you doing today?"
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

- [Model Playground](https://fal.ai/models/fal-ai/flashhead)
- [API Documentation](https://fal.ai/models/fal-ai/flashhead/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/flashhead)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
