# AI Avatar Multi Text

> MultiTalk model generates a multi-person conversation video from an image and text inputs. Converts text to speech for each person, generating a realistic conversation scene.


## Overview

- **Endpoint**: `https://fal.run/fal-ai/ai-avatar/multi-text`
- **Model ID**: `fal-ai/ai-avatar/multi-text`
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
  - Examples: "https://v3.fal.media/files/koala/vhkIF86hmgNTBll_lF1xI_3c7476642b19435aa763fe3b49cf99c7.png"

- **`first_text_input`** (`string`, _required_):
  The text input to guide video generation.
  - Examples: "Do you know what are we eating?"

- **`second_text_input`** (`string`, _required_):
  The text input to guide video generation.
  - Examples: "I dont know I am eating this because our mother gave it to us. I think it is something called milky pie."

- **`voice1`** (`Voice1Enum`, _optional_):
  The first person's voice to use for speech generation Default value: `"Sarah"`
  - Default: `"Sarah"`
  - Options: `"Aria"`, `"Roger"`, `"Sarah"`, `"Laura"`, `"Charlie"`, `"George"`, `"Callum"`, `"River"`, `"Liam"`, `"Charlotte"`, `"Alice"`, `"Matilda"`, `"Will"`, `"Jessica"`, `"Eric"`, `"Chris"`, `"Brian"`, `"Daniel"`, `"Lily"`, `"Bill"`

- **`voice2`** (`Voice2Enum`, _optional_):
  The second person's voice to use for speech generation Default value: `"Roger"`
  - Default: `"Roger"`
  - Options: `"Aria"`, `"Roger"`, `"Sarah"`, `"Laura"`, `"Charlie"`, `"George"`, `"Callum"`, `"River"`, `"Liam"`, `"Charlotte"`, `"Alice"`, `"Matilda"`, `"Will"`, `"Jessica"`, `"Eric"`, `"Chris"`, `"Brian"`, `"Daniel"`, `"Lily"`, `"Bill"`

- **`prompt`** (`string`, _required_):
  The text prompt to guide video generation.
  - Examples: "Two kids talking on a lunch."

- **`num_frames`** (`integer`, _optional_):
  Number of frames to generate. Must be between 81 to 129 (inclusive). If the number of frames is greater than 81, the video will be generated with 1.25x more billing units. Default value: `191`
  - Default: `191`
  - Range: `41` to `241`

- **`resolution`** (`ResolutionEnum`, _optional_):
  Resolution of the video to generate. Must be either 480p or 720p. Default value: `"480p"`
  - Default: `"480p"`
  - Options: `"480p"`, `"720p"`

- **`seed`** (`integer`, _optional_):
  Random seed for reproducibility. If None, a random seed is chosen. Default value: `81`
  - Default: `81`
  - Range: `0` to `4294967295`

- **`acceleration`** (`AccelerationEnum`, _optional_):
  The acceleration level to use for generation. Default value: `"regular"`
  - Default: `"regular"`
  - Options: `"none"`, `"regular"`, `"high"`



**Required Parameters Example**:

```json
{
  "image_url": "https://v3.fal.media/files/koala/vhkIF86hmgNTBll_lF1xI_3c7476642b19435aa763fe3b49cf99c7.png",
  "first_text_input": "Do you know what are we eating?",
  "second_text_input": "I dont know I am eating this because our mother gave it to us. I think it is something called milky pie.",
  "prompt": "Two kids talking on a lunch."
}
```

**Full Example**:

```json
{
  "image_url": "https://v3.fal.media/files/koala/vhkIF86hmgNTBll_lF1xI_3c7476642b19435aa763fe3b49cf99c7.png",
  "first_text_input": "Do you know what are we eating?",
  "second_text_input": "I dont know I am eating this because our mother gave it to us. I think it is something called milky pie.",
  "voice1": "Sarah",
  "voice2": "Roger",
  "prompt": "Two kids talking on a lunch.",
  "num_frames": 191,
  "resolution": "480p",
  "seed": 81,
  "acceleration": "regular"
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`File`, _required_):
  The generated video file.
  - Examples: {"file_name":"30b76b90c2164f9a926527497c20832b.mp4","url":"https://v3.fal.media/files/zebra/lKMkUvzCqKn-gHC0vyUPP_30b76b90c2164f9a926527497c20832b.mp4","file_size":352679,"content_type":"application/octet-stream"}

- **`seed`** (`integer`, _required_):
  The seed used for generation.



**Example Response**:

```json
{
  "video": {
    "file_name": "30b76b90c2164f9a926527497c20832b.mp4",
    "url": "https://v3.fal.media/files/zebra/lKMkUvzCqKn-gHC0vyUPP_30b76b90c2164f9a926527497c20832b.mp4",
    "file_size": 352679,
    "content_type": "application/octet-stream"
  }
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/ai-avatar/multi-text \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "image_url": "https://v3.fal.media/files/koala/vhkIF86hmgNTBll_lF1xI_3c7476642b19435aa763fe3b49cf99c7.png",
     "first_text_input": "Do you know what are we eating?",
     "second_text_input": "I dont know I am eating this because our mother gave it to us. I think it is something called milky pie.",
     "prompt": "Two kids talking on a lunch."
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
    "fal-ai/ai-avatar/multi-text",
    arguments={
        "image_url": "https://v3.fal.media/files/koala/vhkIF86hmgNTBll_lF1xI_3c7476642b19435aa763fe3b49cf99c7.png",
        "first_text_input": "Do you know what are we eating?",
        "second_text_input": "I dont know I am eating this because our mother gave it to us. I think it is something called milky pie.",
        "prompt": "Two kids talking on a lunch."
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

const result = await fal.subscribe("fal-ai/ai-avatar/multi-text", {
  input: {
    image_url: "https://v3.fal.media/files/koala/vhkIF86hmgNTBll_lF1xI_3c7476642b19435aa763fe3b49cf99c7.png",
    first_text_input: "Do you know what are we eating?",
    second_text_input: "I dont know I am eating this because our mother gave it to us. I think it is something called milky pie.",
    prompt: "Two kids talking on a lunch."
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

- [Model Playground](https://fal.ai/models/fal-ai/ai-avatar/multi-text)
- [API Documentation](https://fal.ai/models/fal-ai/ai-avatar/multi-text/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/ai-avatar/multi-text)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
