# Vidu

> Use vidu Text-to-Image to turn your prompts into reality.


## Overview

- **Endpoint**: `https://fal.run/fal-ai/vidu/q2/text-to-image`
- **Model ID**: `fal-ai/vidu/q2/text-to-image`
- **Category**: text-to-image
- **Kind**: inference


## Pricing

Your request will cost $0.1 per image.

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _required_):
  Text prompt for video generation, max 1500 characters
  - Examples: "A majestic dragon perches on the mountaintop, its eyes fixed intently on a small baby dragon."

- **`aspect_ratio`** (`AspectRatioEnum`, _optional_):
  The aspect ratio of the output video Default value: `"16:9"`
  - Default: `"16:9"`
  - Options: `"16:9"`, `"9:16"`, `"1:1"`

- **`seed`** (`integer`, _optional_):
  Random seed for generation



**Required Parameters Example**:

```json
{
  "prompt": "A majestic dragon perches on the mountaintop, its eyes fixed intently on a small baby dragon."
}
```

**Full Example**:

```json
{
  "prompt": "A majestic dragon perches on the mountaintop, its eyes fixed intently on a small baby dragon.",
  "aspect_ratio": "16:9"
}
```


### Output Schema

The API returns the following output format:

- **`image`** (`Image`, _required_):
  The edited image
  - Examples: {"url":"https://storage.googleapis.com/falserverless/videos/general-1-2025-12-02T14_55_54Z.png"}



**Example Response**:

```json
{
  "image": {
    "url": "https://storage.googleapis.com/falserverless/videos/general-1-2025-12-02T14_55_54Z.png"
  }
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/vidu/q2/text-to-image \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "A majestic dragon perches on the mountaintop, its eyes fixed intently on a small baby dragon."
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
    "fal-ai/vidu/q2/text-to-image",
    arguments={
        "prompt": "A majestic dragon perches on the mountaintop, its eyes fixed intently on a small baby dragon."
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

const result = await fal.subscribe("fal-ai/vidu/q2/text-to-image", {
  input: {
    prompt: "A majestic dragon perches on the mountaintop, its eyes fixed intently on a small baby dragon."
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

- [Model Playground](https://fal.ai/models/fal-ai/vidu/q2/text-to-image)
- [API Documentation](https://fal.ai/models/fal-ai/vidu/q2/text-to-image/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/vidu/q2/text-to-image)

### fal.ai Platform

- [Platform Documentation](https://docs.fal.ai)
- [Python Client](https://docs.fal.ai/clients/python)
- [JavaScript Client](https://docs.fal.ai/clients/javascript)
