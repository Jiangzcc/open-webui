# AMT Frame Interpolation

> Interpolate between image frames


## Overview

- **Endpoint**: `https://fal.run/fal-ai/amt-interpolation/frame-interpolation`
- **Model ID**: `fal-ai/amt-interpolation/frame-interpolation`
- **Category**: image-to-video
- **Kind**: inference
**Tags**: interpolation, editing



## Pricing

- **Price**: $0 per compute seconds

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`frames`** (`list<Frame>`, _required_):
  Frames to interpolate
  - Array of Frame
  - Examples: [{"url":"https://storage.googleapis.com/falserverless/model_tests/amt-interpolation/start.png"},{"url":"https://storage.googleapis.com/falserverless/model_tests/amt-interpolation/end.png"}]

- **`output_fps`** (`integer`, _optional_):
  Output frames per second Default value: `24`
  - Default: `24`

- **`recursive_interpolation_passes`** (`integer`, _optional_):
  Number of recursive interpolation passes Default value: `4`
  - Default: `4`



**Required Parameters Example**:

```json
{
  "frames": [
    {
      "url": "https://storage.googleapis.com/falserverless/model_tests/amt-interpolation/start.png"
    },
    {
      "url": "https://storage.googleapis.com/falserverless/model_tests/amt-interpolation/end.png"
    }
  ]
}
```

**Full Example**:

```json
{
  "frames": [
    {
      "url": "https://storage.googleapis.com/falserverless/model_tests/amt-interpolation/start.png"
    },
    {
      "url": "https://storage.googleapis.com/falserverless/model_tests/amt-interpolation/end.png"
    }
  ],
  "output_fps": 24,
  "recursive_interpolation_passes": 4
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`File`, _required_):
  Generated video



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
  --url https://fal.run/fal-ai/amt-interpolation/frame-interpolation \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "frames": [
       {
         "url": "https://storage.googleapis.com/falserverless/model_tests/amt-interpolation/start.png"
       },
       {
         "url": "https://storage.googleapis.com/falserverless/model_tests/amt-interpolation/end.png"
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
    "fal-ai/amt-interpolation/frame-interpolation",
    arguments={
        "frames": [{
            "url": "https://storage.googleapis.com/falserverless/model_tests/amt-interpolation/start.png"
        }, {
            "url": "https://storage.googleapis.com/falserverless/model_tests/amt-interpolation/end.png"
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

const result = await fal.subscribe("fal-ai/amt-interpolation/frame-interpolation", {
  input: {
    frames: [{
      url: "https://storage.googleapis.com/falserverless/model_tests/amt-interpolation/start.png"
    }, {
      url: "https://storage.googleapis.com/falserverless/model_tests/amt-interpolation/end.png"
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

- [Model Playground](https://fal.ai/models/fal-ai/amt-interpolation/frame-interpolation)
- [API Documentation](https://fal.ai/models/fal-ai/amt-interpolation/frame-interpolation/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/amt-interpolation/frame-interpolation)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
