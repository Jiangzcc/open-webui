# Bagel

> Bagel is a 7B parameter from Bytedance-Seed multimodal model that can generate both text and images.


## Overview

- **Endpoint**: `https://fal.run/fal-ai/bagel`
- **Model ID**: `fal-ai/bagel`
- **Category**: text-to-image
- **Kind**: inference
**Tags**: text-to-image, multimodal



## Pricing

- **Price**: $0.1 per images

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _required_):
  The prompt to generate an image from.
  - Examples: "A luminous ancient temple floating among cosmic clouds, with impossible architecture of twisted spires and inverted arches. The structure is half-built from crystalline white marble and half from living bioluminescent coral in vibrant teal and purple. Ethereal light filters through stained glass windows depicting mythological scenes. Tiny cloaked figures with glowing lanterns traverse impossible staircases. In the foreground, a massive ornate door stands slightly ajar, revealing a glimpse of swirling golden energy within. The scene is lit by two moons of different colors, casting overlapping shadows. Cinematic lighting, hyper-detailed textures, 8K resolution."

- **`seed`** (`integer`, _optional_):
  The seed to use for the generation.

- **`use_thought`** (`boolean`, _optional_):
  Whether to use thought tokens for generation. If set to true, the model will "think" to potentially improve generation quality. Increases generation time and increases the cost by 20%.
  - Default: `false`

- **`enable_safety_checker`** (`boolean`, _optional_):
  If set to true, the safety checker will be enabled. Default value: `true`
  - Default: `true`



**Required Parameters Example**:

```json
{
  "prompt": "A luminous ancient temple floating among cosmic clouds, with impossible architecture of twisted spires and inverted arches. The structure is half-built from crystalline white marble and half from living bioluminescent coral in vibrant teal and purple. Ethereal light filters through stained glass windows depicting mythological scenes. Tiny cloaked figures with glowing lanterns traverse impossible staircases. In the foreground, a massive ornate door stands slightly ajar, revealing a glimpse of swirling golden energy within. The scene is lit by two moons of different colors, casting overlapping shadows. Cinematic lighting, hyper-detailed textures, 8K resolution."
}
```

**Full Example**:

```json
{
  "prompt": "A luminous ancient temple floating among cosmic clouds, with impossible architecture of twisted spires and inverted arches. The structure is half-built from crystalline white marble and half from living bioluminescent coral in vibrant teal and purple. Ethereal light filters through stained glass windows depicting mythological scenes. Tiny cloaked figures with glowing lanterns traverse impossible staircases. In the foreground, a massive ornate door stands slightly ajar, revealing a glimpse of swirling golden energy within. The scene is lit by two moons of different colors, casting overlapping shadows. Cinematic lighting, hyper-detailed textures, 8K resolution.",
  "enable_safety_checker": true
}
```


### Output Schema

The API returns the following output format:

- **`images`** (`list<Image>`, _required_):
  The generated images.
  - Array of Image
  - Examples: [{"width":1024,"content_type":"image/jpeg","url":"https://storage.googleapis.com/falserverless/bagel/wRhCPSyiKTiLnnWvUpGIl.jpeg","file_name":"wRhCPSyiKTiLnnWvUpGIl.jpeg","file_size":423052,"height":1024}]

- **`timings`** (`Timings`, _required_)

- **`seed`** (`integer`, _required_):
  Seed of the generated Image. It will be the same value of the one passed in the
  input or the randomly generated that was used in case none was passed.

- **`has_nsfw_concepts`** (`list<boolean>`, _required_):
  Whether the generated images contain NSFW concepts.
  - Array of boolean

- **`prompt`** (`string`, _required_):
  The prompt used for generating the image.



**Example Response**:

```json
{
  "images": [
    {
      "width": 1024,
      "content_type": "image/jpeg",
      "url": "https://storage.googleapis.com/falserverless/bagel/wRhCPSyiKTiLnnWvUpGIl.jpeg",
      "file_name": "wRhCPSyiKTiLnnWvUpGIl.jpeg",
      "file_size": 423052,
      "height": 1024
    }
  ],
  "prompt": ""
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/bagel \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "A luminous ancient temple floating among cosmic clouds, with impossible architecture of twisted spires and inverted arches. The structure is half-built from crystalline white marble and half from living bioluminescent coral in vibrant teal and purple. Ethereal light filters through stained glass windows depicting mythological scenes. Tiny cloaked figures with glowing lanterns traverse impossible staircases. In the foreground, a massive ornate door stands slightly ajar, revealing a glimpse of swirling golden energy within. The scene is lit by two moons of different colors, casting overlapping shadows. Cinematic lighting, hyper-detailed textures, 8K resolution."
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
    "fal-ai/bagel",
    arguments={
        "prompt": "A luminous ancient temple floating among cosmic clouds, with impossible architecture of twisted spires and inverted arches. The structure is half-built from crystalline white marble and half from living bioluminescent coral in vibrant teal and purple. Ethereal light filters through stained glass windows depicting mythological scenes. Tiny cloaked figures with glowing lanterns traverse impossible staircases. In the foreground, a massive ornate door stands slightly ajar, revealing a glimpse of swirling golden energy within. The scene is lit by two moons of different colors, casting overlapping shadows. Cinematic lighting, hyper-detailed textures, 8K resolution."
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

const result = await fal.subscribe("fal-ai/bagel", {
  input: {
    prompt: "A luminous ancient temple floating among cosmic clouds, with impossible architecture of twisted spires and inverted arches. The structure is half-built from crystalline white marble and half from living bioluminescent coral in vibrant teal and purple. Ethereal light filters through stained glass windows depicting mythological scenes. Tiny cloaked figures with glowing lanterns traverse impossible staircases. In the foreground, a massive ornate door stands slightly ajar, revealing a glimpse of swirling golden energy within. The scene is lit by two moons of different colors, casting overlapping shadows. Cinematic lighting, hyper-detailed textures, 8K resolution."
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

- [Model Playground](https://fal.ai/models/fal-ai/bagel)
- [API Documentation](https://fal.ai/models/fal-ai/bagel/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/bagel)

### fal.ai Platform

- [Platform Documentation](https://docs.fal.ai)
- [Python Client](https://docs.fal.ai/clients/python)
- [JavaScript Client](https://docs.fal.ai/clients/javascript)
