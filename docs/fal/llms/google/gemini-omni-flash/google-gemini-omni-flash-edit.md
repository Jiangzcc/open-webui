# Gemini Omni Flash

> Edits generated video across multiple conversational turns while preserving scene coherence. Applies iterative changes through natural-language instructions without regenerating the full sequence from scratch.


## Overview

- **Endpoint**: `https://fal.run/google/gemini-omni-flash/edit`
- **Model ID**: `google/gemini-omni-flash/edit`
- **Category**: video-to-video
- **Kind**: inference
**Tags**: stylized, transform, lipsync



## Pricing

Billing is based on **total token consumption**. Input tokens (text/audio/video) cost **$1.875 per 1 million tokens**. Output tokens cost **$21.875 per 1 million tokens**. For 720p video this costs **approximately $0.13 per second of video**. 

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _required_):
  A simple instruction describing the edit. Simple prompts work best; add "Keep everything else the same." to preserve the rest of the scene. Voice editing is not supported.
  - Examples: "Make this video anime. Keep everything else the same."

- **`video_url`** (`string`, _required_):
  URL of the video to edit. Note: editing uploaded videos is not available for users in the European Economic Area (EEA), Switzerland, and the United Kingdom.
  - Examples: "https://storage.googleapis.com/falserverless/model_tests/video_models/mmaudio_input.mp4"



**Required Parameters Example**:

```json
{
  "prompt": "Make this video anime. Keep everything else the same.",
  "video_url": "https://storage.googleapis.com/falserverless/model_tests/video_models/mmaudio_input.mp4"
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`File`, _required_):
  The edited video.



**Example Response**:

```json
{
  "video": {
    "url": "",
    "content_type": "image/png",
    "file_name": "z9RV14K95DvU.png",
    "file_size": 4404019
  }
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/google/gemini-omni-flash/edit \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "Make this video anime. Keep everything else the same.",
     "video_url": "https://storage.googleapis.com/falserverless/model_tests/video_models/mmaudio_input.mp4"
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
    "google/gemini-omni-flash/edit",
    arguments={
        "prompt": "Make this video anime. Keep everything else the same.",
        "video_url": "https://storage.googleapis.com/falserverless/model_tests/video_models/mmaudio_input.mp4"
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

const result = await fal.subscribe("google/gemini-omni-flash/edit", {
  input: {
    prompt: "Make this video anime. Keep everything else the same.",
    video_url: "https://storage.googleapis.com/falserverless/model_tests/video_models/mmaudio_input.mp4"
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

- [Model Playground](https://fal.ai/models/google/gemini-omni-flash/edit)
- [API Documentation](https://fal.ai/models/google/gemini-omni-flash/edit/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=google/gemini-omni-flash/edit)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
