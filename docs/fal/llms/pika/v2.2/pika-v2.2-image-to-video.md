# Pika Image to Video (v2.2)

> Turn photos into mind-blowing, dynamic videos in up to 1080p. Experience better image clarity and crisper, sharper visuals.


## Overview

- **Endpoint**: `https://fal.run/fal-ai/pika/v2.2/image-to-video`
- **Model ID**: `fal-ai/pika/v2.2/image-to-video`
- **Category**: image-to-video
- **Kind**: inference
**Tags**: editing, effects, animation



## Pricing

5 second video at 720p costs $0.20. 5 second video at 1080p costs $0.45.

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`image_url`** (`string`, _required_):
  URL of the image to use as the first frame
  - Examples: "https://storage.googleapis.com/falserverless/example_inputs/pika/pika_i2v_v22_input.png"

- **`prompt`** (`string`, _required_)
  - Examples: "The man and the horse are slowly walking towards the camera, the camera orbits and dolly out"

- **`seed`** (`integer`, _optional_):
  The seed for the random number generator

- **`negative_prompt`** (`string`, _optional_):
  A negative prompt to guide the model Default value: `""`
  - Default: `""`

- **`resolution`** (`ResolutionEnum`, _optional_):
  The resolution of the generated video Default value: `"720p"`
  - Default: `"720p"`
  - Options: `"720p"`, `"1080p"`
  - Examples: "1080p", "720p"

- **`duration`** (`DurationEnum`, _optional_):
  The duration of the generated video in seconds Default value: `"5"`
  - Default: `5`
  - Options: `5`, `10`



**Required Parameters Example**:

```json
{
  "image_url": "https://storage.googleapis.com/falserverless/example_inputs/pika/pika_i2v_v22_input.png",
  "prompt": "The man and the horse are slowly walking towards the camera, the camera orbits and dolly out"
}
```

**Full Example**:

```json
{
  "image_url": "https://storage.googleapis.com/falserverless/example_inputs/pika/pika_i2v_v22_input.png",
  "prompt": "The man and the horse are slowly walking towards the camera, the camera orbits and dolly out",
  "resolution": "1080p",
  "duration": 5
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`File`, _required_):
  The generated video
  - Examples: {"url":"https://storage.googleapis.com/falserverless/example_outputs/pika/pika_i2v_v22_output.mp4"}



**Example Response**:

```json
{
  "video": {
    "url": "https://storage.googleapis.com/falserverless/example_outputs/pika/pika_i2v_v22_output.mp4"
  }
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/pika/v2.2/image-to-video \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "image_url": "https://storage.googleapis.com/falserverless/example_inputs/pika/pika_i2v_v22_input.png",
     "prompt": "The man and the horse are slowly walking towards the camera, the camera orbits and dolly out"
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
    "fal-ai/pika/v2.2/image-to-video",
    arguments={
        "image_url": "https://storage.googleapis.com/falserverless/example_inputs/pika/pika_i2v_v22_input.png",
        "prompt": "The man and the horse are slowly walking towards the camera, the camera orbits and dolly out"
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

const result = await fal.subscribe("fal-ai/pika/v2.2/image-to-video", {
  input: {
    image_url: "https://storage.googleapis.com/falserverless/example_inputs/pika/pika_i2v_v22_input.png",
    prompt: "The man and the horse are slowly walking towards the camera, the camera orbits and dolly out"
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

- [Model Playground](https://fal.ai/models/fal-ai/pika/v2.2/image-to-video)
- [API Documentation](https://fal.ai/models/fal-ai/pika/v2.2/image-to-video/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/pika/v2.2/image-to-video)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
