# AI Avatar Single Text

> MultiTalk model generates a talking avatar video from an image and text. Converts text to speech automatically, then generates the avatar speaking with lip-sync.


## Overview

- **Endpoint**: `https://fal.run/fal-ai/ai-avatar/single-text`
- **Model ID**: `fal-ai/ai-avatar/single-text`
- **Category**: image-to-video
- **Kind**: inference
**Tags**: stylized, transform



## Pricing

- **Price**: $0.2 per seconds

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`image_url`** (`string`, _required_):
  URL of the input image. If the input image does not match the chosen aspect ratio, it is resized and center cropped.
  - Examples: "https://v3.fal.media/files/panda/HuM21CXMf0q7OO2zbvwhV_c4533aada79a495b90e50e32dc9b83a8.png"

- **`text_input`** (`string`, _required_):
  The text input to guide video generation.
  - Examples: "Spend more time with people who make you feel alive, and less with things that drain your soul."

- **`voice`** (`VoiceEnum`, _required_):
  The voice to use for speech generation
  - Options: `"Aria"`, `"Roger"`, `"Sarah"`, `"Laura"`, `"Charlie"`, `"George"`, `"Callum"`, `"River"`, `"Liam"`, `"Charlotte"`, `"Alice"`, `"Matilda"`, `"Will"`, `"Jessica"`, `"Eric"`, `"Chris"`, `"Brian"`, `"Daniel"`, `"Lily"`, `"Bill"`
  - Examples: "Bill"

- **`prompt`** (`string`, _required_):
  The text prompt to guide video generation.
  - Examples: "An elderly man with a white beard and headphones records audio with a microphone. He appears engaged and expressive, suggesting a podcast or voiceover."

- **`num_frames`** (`integer`, _optional_):
  Number of frames to generate. Must be between 41 to 721. Default value: `145`
  - Default: `145`
  - Range: `41` to `721`

- **`resolution`** (`ResolutionEnum`, _optional_):
  Resolution of the video to generate. Must be either 480p or 720p. Default value: `"480p"`
  - Default: `"480p"`
  - Options: `"480p"`, `"720p"`

- **`seed`** (`integer`, _optional_):
  Random seed for reproducibility. If None, a random seed is chosen. Default value: `42`
  - Default: `42`
  - Range: `0` to `4294967295`

- **`acceleration`** (`AccelerationEnum`, _optional_):
  The acceleration level to use for generation. Default value: `"regular"`
  - Default: `"regular"`
  - Options: `"none"`, `"regular"`, `"high"`



**Required Parameters Example**:

```json
{
  "image_url": "https://v3.fal.media/files/panda/HuM21CXMf0q7OO2zbvwhV_c4533aada79a495b90e50e32dc9b83a8.png",
  "text_input": "Spend more time with people who make you feel alive, and less with things that drain your soul.",
  "voice": "Bill",
  "prompt": "An elderly man with a white beard and headphones records audio with a microphone. He appears engaged and expressive, suggesting a podcast or voiceover."
}
```

**Full Example**:

```json
{
  "image_url": "https://v3.fal.media/files/panda/HuM21CXMf0q7OO2zbvwhV_c4533aada79a495b90e50e32dc9b83a8.png",
  "text_input": "Spend more time with people who make you feel alive, and less with things that drain your soul.",
  "voice": "Bill",
  "prompt": "An elderly man with a white beard and headphones records audio with a microphone. He appears engaged and expressive, suggesting a podcast or voiceover.",
  "num_frames": 145,
  "resolution": "480p",
  "seed": 42,
  "acceleration": "regular"
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`File`, _required_):
  The generated video file.
  - Examples: {"file_name":"6c9dd31e1d9a4482877747a52a661a0a.mp4","url":"https://v3.fal.media/files/elephant/-huMN0zTaXmBr2CqzCMps_6c9dd31e1d9a4482877747a52a661a0a.mp4","file_size":797478,"content_type":"application/octet-stream"}

- **`seed`** (`integer`, _required_):
  The seed used for generation.



**Example Response**:

```json
{
  "video": {
    "file_name": "6c9dd31e1d9a4482877747a52a661a0a.mp4",
    "url": "https://v3.fal.media/files/elephant/-huMN0zTaXmBr2CqzCMps_6c9dd31e1d9a4482877747a52a661a0a.mp4",
    "file_size": 797478,
    "content_type": "application/octet-stream"
  }
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/ai-avatar/single-text \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "image_url": "https://v3.fal.media/files/panda/HuM21CXMf0q7OO2zbvwhV_c4533aada79a495b90e50e32dc9b83a8.png",
     "text_input": "Spend more time with people who make you feel alive, and less with things that drain your soul.",
     "voice": "Bill",
     "prompt": "An elderly man with a white beard and headphones records audio with a microphone. He appears engaged and expressive, suggesting a podcast or voiceover."
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
    "fal-ai/ai-avatar/single-text",
    arguments={
        "image_url": "https://v3.fal.media/files/panda/HuM21CXMf0q7OO2zbvwhV_c4533aada79a495b90e50e32dc9b83a8.png",
        "text_input": "Spend more time with people who make you feel alive, and less with things that drain your soul.",
        "voice": "Bill",
        "prompt": "An elderly man with a white beard and headphones records audio with a microphone. He appears engaged and expressive, suggesting a podcast or voiceover."
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

const result = await fal.subscribe("fal-ai/ai-avatar/single-text", {
  input: {
    image_url: "https://v3.fal.media/files/panda/HuM21CXMf0q7OO2zbvwhV_c4533aada79a495b90e50e32dc9b83a8.png",
    text_input: "Spend more time with people who make you feel alive, and less with things that drain your soul.",
    voice: "Bill",
    prompt: "An elderly man with a white beard and headphones records audio with a microphone. He appears engaged and expressive, suggesting a podcast or voiceover."
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

- [Model Playground](https://fal.ai/models/fal-ai/ai-avatar/single-text)
- [API Documentation](https://fal.ai/models/fal-ai/ai-avatar/single-text/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/ai-avatar/single-text)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
