# PixVerse Sound Effects

> Add immersive sound effects and background music to your videos using PixVerse sound effects  generation


## Overview

- **Endpoint**: `https://fal.run/fal-ai/pixverse/sound-effects`
- **Model ID**: `fal-ai/pixverse/sound-effects`
- **Category**: video-to-video
- **Kind**: inference
**Tags**: audio, utility



## Pricing

- **Price**: $0.1 per 5 seconds

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`video_url`** (`string`, _required_):
  URL of the input video to add sound effects to
  - Examples: "https://v3.fal.media/files/tiger/QfpJmEBkR75KpB6yfNLDM_video.mp4"

- **`original_sound_switch`** (`boolean`, _optional_):
  Whether to keep the original audio from the video
  - Default: `false`

- **`prompt`** (`string`, _optional_):
  Description of the sound effect to generate. If empty, a random sound effect will be generated Default value: `""`
  - Default: `""`
  - Examples: "sea waves", "thunder storm", "birds chirping"



**Required Parameters Example**:

```json
{
  "video_url": "https://v3.fal.media/files/tiger/QfpJmEBkR75KpB6yfNLDM_video.mp4"
}
```

**Full Example**:

```json
{
  "video_url": "https://v3.fal.media/files/tiger/QfpJmEBkR75KpB6yfNLDM_video.mp4",
  "prompt": "sea waves"
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`File`, _required_):
  The video with added sound effects
  - Examples: {"file_size":1534052,"file_name":"output.mp4","content_type":"video/mp4","url":"https://v3.fal.media/files/kangaroo/bBQr_DUeICo6_Ty_b_Y0I_output.mp4"}



**Example Response**:

```json
{
  "video": {
    "file_size": 1534052,
    "file_name": "output.mp4",
    "content_type": "video/mp4",
    "url": "https://v3.fal.media/files/kangaroo/bBQr_DUeICo6_Ty_b_Y0I_output.mp4"
  }
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/pixverse/sound-effects \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "video_url": "https://v3.fal.media/files/tiger/QfpJmEBkR75KpB6yfNLDM_video.mp4"
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
    "fal-ai/pixverse/sound-effects",
    arguments={
        "video_url": "https://v3.fal.media/files/tiger/QfpJmEBkR75KpB6yfNLDM_video.mp4"
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

const result = await fal.subscribe("fal-ai/pixverse/sound-effects", {
  input: {
    video_url: "https://v3.fal.media/files/tiger/QfpJmEBkR75KpB6yfNLDM_video.mp4"
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

- [Model Playground](https://fal.ai/models/fal-ai/pixverse/sound-effects)
- [API Documentation](https://fal.ai/models/fal-ai/pixverse/sound-effects/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/pixverse/sound-effects)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
