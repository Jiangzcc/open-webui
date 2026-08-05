# Gemini Omni Flash

> Creates video with synchronized audio from text input. Grounded in Gemini's real-world knowledge, with improved physics understanding for more coherent motion and interaction.


## Overview

- **Endpoint**: `https://fal.run/google/gemini-omni-flash`
- **Model ID**: `google/gemini-omni-flash`
- **Category**: text-to-video
- **Kind**: inference
**Tags**: stylized, transform, lipsync



## Pricing

Billing is based on **total token consumption**. Tokens cost **$21.875 per 1 million tokens**. For 720p video this costs **approximately $0.125 per second of video**. 

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _required_):
  The text prompt describing the video you want to generate.
  - Examples: "A cinematic wide shot of a lighthouse on a rocky cliff at dusk, waves crashing below, the beam slowly sweeping across the dark sea."

- **`aspect_ratio`** (`AspectRatioEnum`, _optional_):
  The aspect ratio of the generated video. Default value: `"16:9"`
  - Default: `"16:9"`
  - Options: `"16:9"`, `"9:16"`

- **`duration`** (`integer`, _optional_):
  The duration of the generated video, in seconds. Default value: `8`
  - Default: `8`
  - Range: `3` to `10`



**Required Parameters Example**:

```json
{
  "prompt": "A cinematic wide shot of a lighthouse on a rocky cliff at dusk, waves crashing below, the beam slowly sweeping across the dark sea."
}
```

**Full Example**:

```json
{
  "prompt": "A cinematic wide shot of a lighthouse on a rocky cliff at dusk, waves crashing below, the beam slowly sweeping across the dark sea.",
  "aspect_ratio": "16:9",
  "duration": 8
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`File`, _required_):
  The generated video.



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
  --url https://fal.run/google/gemini-omni-flash \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "A cinematic wide shot of a lighthouse on a rocky cliff at dusk, waves crashing below, the beam slowly sweeping across the dark sea."
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
    "google/gemini-omni-flash",
    arguments={
        "prompt": "A cinematic wide shot of a lighthouse on a rocky cliff at dusk, waves crashing below, the beam slowly sweeping across the dark sea."
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

const result = await fal.subscribe("google/gemini-omni-flash", {
  input: {
    prompt: "A cinematic wide shot of a lighthouse on a rocky cliff at dusk, waves crashing below, the beam slowly sweeping across the dark sea."
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

- [Model Playground](https://fal.ai/models/google/gemini-omni-flash)
- [API Documentation](https://fal.ai/models/google/gemini-omni-flash/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=google/gemini-omni-flash)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
