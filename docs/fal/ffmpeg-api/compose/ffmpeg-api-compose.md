# FFmpeg API Compose

> Compose videos from multiple media sources using FFmpeg API.


## Overview

- **Endpoint**: `https://fal.run/fal-ai/ffmpeg-api/compose`
- **Model ID**: `fal-ai/ffmpeg-api/compose`
- **Category**: video-to-video
- **Kind**: inference
**Tags**: ffmpeg



## Pricing

- **Price**: $0.0002 per seconds

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`tracks`** (`list<Track>`, _required_):
  List of tracks to be combined into the final media
  - Array of Track



**Required Parameters Example**:

```json
{
  "tracks": [
    {
      "id": "",
      "type": "",
      "keyframes": [
        {
          "url": ""
        }
      ]
    }
  ]
}
```


### Output Schema

The API returns the following output format:

- **`video_url`** (`string`, _required_):
  URL of the processed video file

- **`thumbnail_url`** (`string`, _required_):
  URL of the video's thumbnail image



**Example Response**:

```json
{
  "video_url": "",
  "thumbnail_url": ""
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/ffmpeg-api/compose \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "tracks": [
       {
         "id": "",
         "type": "",
         "keyframes": [
           {
             "url": ""
           }
         ]
       }
     ]
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
    "fal-ai/ffmpeg-api/compose",
    arguments={
        "tracks": [{
            "id": "",
            "type": "",
            "keyframes": [{
                "url": ""
            }]
        }]
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

const result = await fal.subscribe("fal-ai/ffmpeg-api/compose", {
  input: {
    tracks: [{
      id: "",
      type: "",
      keyframes: [{
        url: ""
      }]
    }]
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

- [Model Playground](https://fal.ai/models/fal-ai/ffmpeg-api/compose)
- [API Documentation](https://fal.ai/models/fal-ai/ffmpeg-api/compose/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/ffmpeg-api/compose)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
