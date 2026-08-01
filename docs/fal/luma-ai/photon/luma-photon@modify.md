# Luma Photon

> Edit images from your prompts using Luma Photon. Photon is the most creative, personalizable, and intelligent visual models for creatives, bringing a step-function change in the cost of high-quality image generation.


## Overview

- **Endpoint**: `https://fal.run/fal-ai/luma-photon/modify`
- **Model ID**: `fal-ai/luma-photon/modify`
- **Category**: image-to-image
- **Kind**: inference
**Tags**: image-to-image



## Pricing

- **Price**: $0.019 per megapixels

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _optional_):
  Instruction for modifying the image
  - Examples: "Make the image look like a painting"

- **`image_url`** (`string`, _required_):
  URL of the input image to reframe
  - Examples: "https://storage.googleapis.com/falserverless/gallery/example_inputs_liuyifei.png"

- **`strength`** (`float`, _required_):
  The strength of the initial image. Higher strength values are corresponding to more influence of the initial image on the output.
  - Range: `0` to `1`
  - Examples: 0.8

- **`aspect_ratio`** (`AspectRatioEnum`, _required_):
  The aspect ratio of the reframed image
  - Options: `"1:1"`, `"16:9"`, `"9:16"`, `"4:3"`, `"3:4"`, `"21:9"`, `"9:21"`
  - Examples: "16:9"



**Required Parameters Example**:

```json
{
  "image_url": "https://storage.googleapis.com/falserverless/gallery/example_inputs_liuyifei.png",
  "strength": 0.8,
  "aspect_ratio": "16:9"
}
```

**Full Example**:

```json
{
  "prompt": "Make the image look like a painting",
  "image_url": "https://storage.googleapis.com/falserverless/gallery/example_inputs_liuyifei.png",
  "strength": 0.8,
  "aspect_ratio": "16:9"
}
```


### Output Schema

The API returns the following output format:

- **`images`** (`list<File>`, _required_):
  The generated image
  - Array of File



**Example Response**:

```json
{
  "images": [
    {
      "url": "",
      "content_type": "image/png",
      "file_name": "z9RV14K95DvU.png",
      "file_size": 4404019
    }
  ]
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/luma-photon/modify \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "image_url": "https://storage.googleapis.com/falserverless/gallery/example_inputs_liuyifei.png",
     "strength": 0.8,
     "aspect_ratio": "16:9"
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
    "fal-ai/luma-photon/modify",
    arguments={
        "image_url": "https://storage.googleapis.com/falserverless/gallery/example_inputs_liuyifei.png",
        "strength": 0.8,
        "aspect_ratio": "16:9"
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

const result = await fal.subscribe("fal-ai/luma-photon/modify", {
  input: {
    image_url: "https://storage.googleapis.com/falserverless/gallery/example_inputs_liuyifei.png",
    strength: 0.8,
    aspect_ratio: "16:9"
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

- [Model Playground](https://fal.ai/models/fal-ai/luma-photon/modify)
- [API Documentation](https://fal.ai/models/fal-ai/luma-photon/modify/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/luma-photon/modify)

### fal.ai Platform

- [Platform Documentation](https://docs.fal.ai)
- [Python Client](https://docs.fal.ai/clients/python)
- [JavaScript Client](https://docs.fal.ai/clients/javascript)