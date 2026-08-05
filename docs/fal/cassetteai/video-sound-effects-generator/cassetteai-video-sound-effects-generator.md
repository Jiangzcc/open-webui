# Video Sound Effects Generator

> Add sound effects to your videos


## Overview

- **Endpoint**: `https://fal.run/cassetteai/video-sound-effects-generator`
- **Model ID**: `cassetteai/video-sound-effects-generator`
- **Category**: video-to-video
- **Kind**: inference
**Tags**: sound-effects, sfx, cassetteai



## Pricing

- **Price**: $0.2 per minutes

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`video_url`** (`Video`, _required_):
  A video file to analyze & re-sound with generated SFX.
  - Examples: "https://v3.fal.media/files/tiger/3NOa3BqrJfr3jJBMqGexs_final_with_sfx.mp4", "https://v3.fal.media/files/rabbit/vkNtbcJ3x7KmzjJZeVWQe_final_with_sfx.mp4"



**Required Parameters Example**:

```json
{
  "video_url": "https://v3.fal.media/files/tiger/3NOa3BqrJfr3jJBMqGexs_final_with_sfx.mp4"
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`File`, _required_):
  The final video with the newly generated SFX track.
  - Examples: {"url":"https://v3.fal.media/files/tiger/3NOa3BqrJfr3jJBMqGexs_final_with_sfx.mp4"}



**Example Response**:

```json
{
  "video": {
    "url": "https://v3.fal.media/files/tiger/3NOa3BqrJfr3jJBMqGexs_final_with_sfx.mp4"
  }
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/cassetteai/video-sound-effects-generator \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "video_url": "https://v3.fal.media/files/tiger/3NOa3BqrJfr3jJBMqGexs_final_with_sfx.mp4"
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
    "cassetteai/video-sound-effects-generator",
    arguments={
        "video_url": "https://v3.fal.media/files/tiger/3NOa3BqrJfr3jJBMqGexs_final_with_sfx.mp4"
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

const result = await fal.subscribe("cassetteai/video-sound-effects-generator", {
  input: {
    video_url: "https://v3.fal.media/files/tiger/3NOa3BqrJfr3jJBMqGexs_final_with_sfx.mp4"
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

- [Model Playground](https://fal.ai/models/cassetteai/video-sound-effects-generator)
- [API Documentation](https://fal.ai/models/cassetteai/video-sound-effects-generator/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=cassetteai/video-sound-effects-generator)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
