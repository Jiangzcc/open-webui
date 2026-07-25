# Recraft V4 Pro (Vector)

> Recraft V4 was developed with designers to bring true visual taste to AI image generation. Built for brand systems and production-ready workflows, it goes beyond prompt accuracy — delivering stronger composition, refined lighting, realistic materials, and a cohesive aesthetic. The result is imagery shaped by professional design judgment, ready for immediate real-world use without additional post-processing.


## Overview

- **Endpoint**: `https://fal.run/fal-ai/recraft/v4/pro/text-to-vector`
- **Model ID**: `fal-ai/recraft/v4/pro/text-to-vector`
- **Category**: text-to-image
- **Kind**: inference
**Tags**: text-to-image, text-to-vector



## Pricing

- **Price**: $0.3 per images

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _required_)
  - Examples: "a cute character panda with cool clothes, 3d flat color, design"

- **`image_size`** (`ImageSize | Enum`, _optional_):
   Default value: `square_hd`
  - Default: `"square_hd"`
  - One of: ImageSize | Enum
  - Examples: "landscape_16_9"

- **`colors`** (`list<RGBColor>`, _optional_):
  An array of preferable colors
  - Default: `[]`
  - Array of RGBColor

- **`background_color`** (`RGBColor`, _optional_):
  The preferable background color of the generated images.

- **`enable_safety_checker`** (`boolean`, _optional_):
  If set to true, the safety checker will be enabled. Default value: `true`
  - Default: `true`



**Required Parameters Example**:

```json
{
  "prompt": "a cute character panda with cool clothes, 3d flat color, design"
}
```

**Full Example**:

```json
{
  "prompt": "a cute character panda with cool clothes, 3d flat color, design",
  "image_size": "landscape_16_9",
  "colors": [],
  "enable_safety_checker": true
}
```


### Output Schema

The API returns the following output format:

- **`images`** (`list<File>`, _required_)
  - Array of File
  - Examples: [{"content_type":"image/svg+xml","file_name":"image.svg","file_size":1818794,"url":"https://v3b.fal.media/files/b/0a8ee4de/lmXuapOPV309mE533swE0_image.svg"}]



**Example Response**:

```json
{
  "images": [
    {
      "content_type": "image/svg+xml",
      "file_name": "image.svg",
      "file_size": 1818794,
      "url": "https://v3b.fal.media/files/b/0a8ee4de/lmXuapOPV309mE533swE0_image.svg"
    }
  ]
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/recraft/v4/pro/text-to-vector \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "a cute character panda with cool clothes, 3d flat color, design"
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
    "fal-ai/recraft/v4/pro/text-to-vector",
    arguments={
        "prompt": "a cute character panda with cool clothes, 3d flat color, design"
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

const result = await fal.subscribe("fal-ai/recraft/v4/pro/text-to-vector", {
  input: {
    prompt: "a cute character panda with cool clothes, 3d flat color, design"
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

- [Model Playground](https://fal.ai/models/fal-ai/recraft/v4/pro/text-to-vector)
- [API Documentation](https://fal.ai/models/fal-ai/recraft/v4/pro/text-to-vector/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/recraft/v4/pro/text-to-vector)

### fal.ai Platform

- [Platform Documentation](https://docs.fal.ai)
- [Python Client](https://docs.fal.ai/clients/python)
- [JavaScript Client](https://docs.fal.ai/clients/javascript)
