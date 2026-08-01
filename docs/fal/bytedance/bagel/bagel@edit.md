# Bagel

> Bagel is a 7B parameter multimodal model from Bytedance-Seed that can generate both images and text.


## Overview

- **Endpoint**: `https://fal.run/fal-ai/bagel/edit`
- **Model ID**: `fal-ai/bagel/edit`
- **Category**: image-to-image
- **Kind**: inference
**Tags**: image-to-image, image-editing



## Pricing

- **Price**: $0.1 per images

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _required_):
  The prompt to edit the image with.
  - Examples: "Change the cosmic cloud background of the floating temple to a clear blue sky with a gentle sunrise on the horizon. Keep all temple architecture, figures, and other elements exactly as they are."

- **`seed`** (`integer`, _optional_):
  The seed to use for the generation.

- **`use_thought`** (`boolean`, _optional_):
  Whether to use thought tokens for generation. If set to true, the model will "think" to potentially improve generation quality. Increases generation time and increases the cost by 20%.
  - Default: `false`

- **`enable_safety_checker`** (`boolean`, _optional_):
  If set to true, the safety checker will be enabled. Default value: `true`
  - Default: `true`

- **`image_url`** (`string`, _required_):
  The image to edit.
  - Examples: "https://storage.googleapis.com/falserverless/bagel/wRhCPSyiKTiLnnWvUpGIl.jpeg"



**Required Parameters Example**:

```json
{
  "prompt": "Change the cosmic cloud background of the floating temple to a clear blue sky with a gentle sunrise on the horizon. Keep all temple architecture, figures, and other elements exactly as they are.",
  "image_url": "https://storage.googleapis.com/falserverless/bagel/wRhCPSyiKTiLnnWvUpGIl.jpeg"
}
```

**Full Example**:

```json
{
  "prompt": "Change the cosmic cloud background of the floating temple to a clear blue sky with a gentle sunrise on the horizon. Keep all temple architecture, figures, and other elements exactly as they are.",
  "enable_safety_checker": true,
  "image_url": "https://storage.googleapis.com/falserverless/bagel/wRhCPSyiKTiLnnWvUpGIl.jpeg"
}
```


### Output Schema

The API returns the following output format:

- **`images`** (`list<Image>`, _required_):
  The edited images.
  - Array of Image
  - Examples: [{"width":1024,"content_type":"image/jpeg","url":"https://storage.googleapis.com/falserverless/bagel/hQnndOMvGSt2UsYAiV3vs.jpeg","file_name":"hQnndOMvGSt2UsYAiV3vs.jpeg","file_size":423052,"height":1024}]

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
      "url": "https://storage.googleapis.com/falserverless/bagel/hQnndOMvGSt2UsYAiV3vs.jpeg",
      "file_name": "hQnndOMvGSt2UsYAiV3vs.jpeg",
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
  --url https://fal.run/fal-ai/bagel/edit \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "Change the cosmic cloud background of the floating temple to a clear blue sky with a gentle sunrise on the horizon. Keep all temple architecture, figures, and other elements exactly as they are.",
     "image_url": "https://storage.googleapis.com/falserverless/bagel/wRhCPSyiKTiLnnWvUpGIl.jpeg"
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
    "fal-ai/bagel/edit",
    arguments={
        "prompt": "Change the cosmic cloud background of the floating temple to a clear blue sky with a gentle sunrise on the horizon. Keep all temple architecture, figures, and other elements exactly as they are.",
        "image_url": "https://storage.googleapis.com/falserverless/bagel/wRhCPSyiKTiLnnWvUpGIl.jpeg"
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

const result = await fal.subscribe("fal-ai/bagel/edit", {
  input: {
    prompt: "Change the cosmic cloud background of the floating temple to a clear blue sky with a gentle sunrise on the horizon. Keep all temple architecture, figures, and other elements exactly as they are.",
    image_url: "https://storage.googleapis.com/falserverless/bagel/wRhCPSyiKTiLnnWvUpGIl.jpeg"
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

- [Model Playground](https://fal.ai/models/fal-ai/bagel/edit)
- [API Documentation](https://fal.ai/models/fal-ai/bagel/edit/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/bagel/edit)

### fal.ai Platform

- [Platform Documentation](https://docs.fal.ai)
- [Python Client](https://docs.fal.ai/clients/python)
- [JavaScript Client](https://docs.fal.ai/clients/javascript)
