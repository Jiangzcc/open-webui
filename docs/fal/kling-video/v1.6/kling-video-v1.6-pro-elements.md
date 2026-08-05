# Kling 1.6 Elements

> Generate video clips from your multiple image references using Kling 1.6 (pro)


## Overview

- **Endpoint**: `https://fal.run/fal-ai/kling-video/v1.6/pro/elements`
- **Model ID**: `fal-ai/kling-video/v1.6/pro/elements`
- **Category**: image-to-video
- **Kind**: inference


## Pricing

- **Price**: $0.098 per seconds

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _required_)
  - Examples: "A cute girl and a baby cow sleeping together on a bed"

- **`input_image_urls`** (`list<string>`, _required_):
  List of image URLs to use for video generation. Supports up to 4 images.
  - Array of string
  - Examples: ["https://storage.googleapis.com/falserverless/web-examples/kling-elements/first_image.jpeg","https://storage.googleapis.com/falserverless/web-examples/kling-elements/second_image.png"]

- **`duration`** (`DurationEnum`, _optional_):
  The duration of the generated video in seconds Default value: `"5"`
  - Default: `"5"`
  - Options: `"5"`, `"10"`

- **`aspect_ratio`** (`AspectRatioEnum`, _optional_):
  The aspect ratio of the generated video frame Default value: `"16:9"`
  - Default: `"16:9"`
  - Options: `"16:9"`, `"9:16"`, `"1:1"`

- **`negative_prompt`** (`string`, _optional_):
   Default value: `"blur, distort, and low quality"`
  - Default: `"blur, distort, and low quality"`



**Required Parameters Example**:

```json
{
  "prompt": "A cute girl and a baby cow sleeping together on a bed",
  "input_image_urls": [
    "https://storage.googleapis.com/falserverless/web-examples/kling-elements/first_image.jpeg",
    "https://storage.googleapis.com/falserverless/web-examples/kling-elements/second_image.png"
  ]
}
```

**Full Example**:

```json
{
  "prompt": "A cute girl and a baby cow sleeping together on a bed",
  "input_image_urls": [
    "https://storage.googleapis.com/falserverless/web-examples/kling-elements/first_image.jpeg",
    "https://storage.googleapis.com/falserverless/web-examples/kling-elements/second_image.png"
  ],
  "duration": "5",
  "aspect_ratio": "16:9",
  "negative_prompt": "blur, distort, and low quality"
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`File`, _required_):
  The generated video
  - Examples: {"file_name":"output.mp4","file_size":3910577,"content_type":"video/mp4","url":"https://v3.fal.media/files/penguin/twy6u1yv09NvqsX0mMFM2_output.mp4"}



**Example Response**:

```json
{
  "video": {
    "file_name": "output.mp4",
    "file_size": 3910577,
    "content_type": "video/mp4",
    "url": "https://v3.fal.media/files/penguin/twy6u1yv09NvqsX0mMFM2_output.mp4"
  }
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/kling-video/v1.6/pro/elements \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "A cute girl and a baby cow sleeping together on a bed",
     "input_image_urls": [
       "https://storage.googleapis.com/falserverless/web-examples/kling-elements/first_image.jpeg",
       "https://storage.googleapis.com/falserverless/web-examples/kling-elements/second_image.png"
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
    "fal-ai/kling-video/v1.6/pro/elements",
    arguments={
        "prompt": "A cute girl and a baby cow sleeping together on a bed",
        "input_image_urls": ["https://storage.googleapis.com/falserverless/web-examples/kling-elements/first_image.jpeg", "https://storage.googleapis.com/falserverless/web-examples/kling-elements/second_image.png"]
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

const result = await fal.subscribe("fal-ai/kling-video/v1.6/pro/elements", {
  input: {
    prompt: "A cute girl and a baby cow sleeping together on a bed",
    input_image_urls: ["https://storage.googleapis.com/falserverless/web-examples/kling-elements/first_image.jpeg", "https://storage.googleapis.com/falserverless/web-examples/kling-elements/second_image.png"]
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

- [Model Playground](https://fal.ai/models/fal-ai/kling-video/v1.6/pro/elements)
- [API Documentation](https://fal.ai/models/fal-ai/kling-video/v1.6/pro/elements/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/kling-video/v1.6/pro/elements)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
