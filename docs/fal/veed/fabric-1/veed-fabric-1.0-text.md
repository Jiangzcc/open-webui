# Fabric 1.0

> VEED Fabric 1.0 text-to-video API


## Overview

- **Endpoint**: `https://fal.run/veed/fabric-1.0/text`
- **Model ID**: `veed/fabric-1.0/text`
- **Category**: text-to-video
- **Kind**: inference
**Tags**: lipsync, avatar, text-to-video



## Pricing

480p - $0.08 per second, 720p - $0.15 per second

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`image_url`** (`string`, _required_)
  - Examples: "https://v3.fal.media/files/koala/NLVPfOI4XL1cWT2PmmqT3_Hope.png"

- **`text`** (`string`, _required_)
  - Examples: "Create talking videos with VEED Fabric-One API."

- **`voice_description`** (`string`, _optional_):
  Optional additional voice description. The primary voice description is auto-generated from the image. You can use simple descriptors like 'British accent' or 'Confident' or provide a detailed description like 'Confident male voice, mid-20s, with notes of...'

- **`resolution`** (`ResolutionEnum`, _required_):
  Resolution
  - Options: `"720p"`, `"480p"`



**Required Parameters Example**:

```json
{
  "image_url": "https://v3.fal.media/files/koala/NLVPfOI4XL1cWT2PmmqT3_Hope.png",
  "text": "Create talking videos with VEED Fabric-One API.",
  "resolution": "720p"
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`File`, _required_)
  - Examples: {"content_type":"audio/mp4","url":"https://v3b.fal.media/files/b/0a8604be/zVkoAB4hTa8g6Fyl6V733_tmpy1fslwp2.mp4"}



**Example Response**:

```json
{
  "video": {
    "content_type": "audio/mp4",
    "url": "https://v3b.fal.media/files/b/0a8604be/zVkoAB4hTa8g6Fyl6V733_tmpy1fslwp2.mp4"
  }
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/veed/fabric-1.0/text \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "image_url": "https://v3.fal.media/files/koala/NLVPfOI4XL1cWT2PmmqT3_Hope.png",
     "text": "Create talking videos with VEED Fabric-One API.",
     "resolution": "720p"
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
    "veed/fabric-1.0/text",
    arguments={
        "image_url": "https://v3.fal.media/files/koala/NLVPfOI4XL1cWT2PmmqT3_Hope.png",
        "text": "Create talking videos with VEED Fabric-One API.",
        "resolution": "720p"
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

const result = await fal.subscribe("veed/fabric-1.0/text", {
  input: {
    image_url: "https://v3.fal.media/files/koala/NLVPfOI4XL1cWT2PmmqT3_Hope.png",
    text: "Create talking videos with VEED Fabric-One API.",
    resolution: "720p"
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

- [Model Playground](https://fal.ai/models/veed/fabric-1.0/text)
- [API Documentation](https://fal.ai/models/veed/fabric-1.0/text/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=veed/fabric-1.0/text)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
