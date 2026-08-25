# Avatars Text to Video

> High-quality avatar videos that feel real, generated from your text


## Overview

- **Endpoint**: `https://fal.run/argil/avatars/text-to-video`
- **Model ID**: `argil/avatars/text-to-video`
- **Category**: text-to-video
- **Kind**: inference


## Pricing

- **Price**: $0.0225 per input seconds

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`avatar`** (`AvatarEnum`, _required_)
  - Options: `"Mia outdoor (UGC)"`, `"Lara (Masterclass)"`, `"Ines (UGC)"`, `"Maria (Masterclass)"`, `"Emma (UGC)"`, `"Sienna (Masterclass)"`, `"Elena (UGC)"`, `"Jasmine (Masterclass)"`, `"Amara (Masterclass)"`, `"Ryan podcast (UGC)"`, `"Tyler (Masterclass)"`, `"Jayse (Masterclass)"`, `"Paul (Masterclass)"`, `"Matteo (UGC)"`, `"Daniel car (UGC)"`, `"Dario (Masterclass)"`, `"Viva (Masterclass)"`, `"Chen (Masterclass)"`, `"Alex (Masterclass)"`, `"Vanessa (UGC)"`, `"Laurent (UGC)"`, `"Noemie car (UGC)"`, `"Brandon (UGC)"`, `"Byron (Masterclass)"`, `"Calista (Masterclass)"`, `"Milo (Masterclass)"`, `"Fabien (Masterclass)"`, `"Rose (UGC)"`
  - Examples: "Noemie car (UGC)"

- **`text`** (`string`, _required_)
  - Examples: "\nArgil is kinda crazy guys! You just turn a real person into \nan avatar that actually talks and moves and it's already reel-ready, \nfor TikTok, Shorts, whatever. No wasting hours editing, it still looks super pro.\n"

- **`voice`** (`VoiceEnum`, _required_)
  - Options: `"Rachel"`, `"Clyde"`, `"Roger"`, `"Sarah"`, `"Laura"`, `"Thomas"`, `"Charlie"`, `"George"`, `"Callum"`, `"River"`, `"Harry"`, `"Liam"`, `"Alice"`, `"Matilda"`, `"Will"`, `"Jessica"`, `"Lilly"`, `"Bill"`, `"Oxley"`, `"Luna"`

- **`remove_background`** (`boolean`, _optional_):
  Enabling the remove background feature will result in a 50% increase in the price.
  - Default: `false`



**Required Parameters Example**:

```json
{
  "avatar": "Noemie car (UGC)",
  "text": "\nArgil is kinda crazy guys! You just turn a real person into \nan avatar that actually talks and moves and it's already reel-ready, \nfor TikTok, Shorts, whatever. No wasting hours editing, it still looks super pro.\n",
  "voice": "Rachel"
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`Video`, _optional_)
  - Examples: {"url":"https://argildotai.s3.us-east-1.amazonaws.com/fal-resource/example_fal.mp4"}

- **`moderation_flagged`** (`boolean`, _optional_)
  - Default: `false`

- **`moderation_transcription`** (`string`, _optional_)

- **`moderation_error`** (`string`, _optional_)



**Example Response**:

```json
{
  "video": {
    "url": "https://argildotai.s3.us-east-1.amazonaws.com/fal-resource/example_fal.mp4"
  }
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/argil/avatars/text-to-video \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "avatar": "Noemie car (UGC)",
     "text": "\nArgil is kinda crazy guys! You just turn a real person into \nan avatar that actually talks and moves and it's already reel-ready, \nfor TikTok, Shorts, whatever. No wasting hours editing, it still looks super pro.\n",
     "voice": "Rachel"
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
    "argil/avatars/text-to-video",
    arguments={
        "avatar": "Noemie car (UGC)",
        "text": "
    Argil is kinda crazy guys! You just turn a real person into
    an avatar that actually talks and moves and it's already reel-ready,
    for TikTok, Shorts, whatever. No wasting hours editing, it still looks super pro.
    ",
        "voice": "Rachel"
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

const result = await fal.subscribe("argil/avatars/text-to-video", {
  input: {
    avatar: "Noemie car (UGC)",
    text: "
  Argil is kinda crazy guys! You just turn a real person into
  an avatar that actually talks and moves and it's already reel-ready,
  for TikTok, Shorts, whatever. No wasting hours editing, it still looks super pro.
  ",
    voice: "Rachel"
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

- [Model Playground](https://fal.ai/models/argil/avatars/text-to-video)
- [API Documentation](https://fal.ai/models/argil/avatars/text-to-video/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=argil/avatars/text-to-video)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
