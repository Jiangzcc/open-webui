# Ideogram

> Train Ideogram on your photos, your style, your subject, your look, from a small set of reference images to images that feel consistently yours 


## Overview

- **Endpoint**: `https://fal.run/fal-ai/ideogram/custom-models/generate`
- **Model ID**: `fal-ai/ideogram/custom-models/generate`
- **Category**: text-to-image
- **Kind**: inference
**Tags**: stylized, transform



## Pricing

Your request will cost **$0.03** with TURBO, **$0.06** with BALANCED, and **$0.09** with QUALITY.

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`model_id`** (`string`, _required_):
  The id of a trained custom model returned by /train. The model must have finished training (status COMPLETED).

- **`prompt`** (`string`, _required_):
  Text prompt describing the image to generate.
  - Examples: "A photo in my custom style"

- **`aspect_ratio`** (`AspectRatioEnum`, _optional_):
  The aspect ratio of the generated image. Default value: `"1:1"`
  - Default: `"1:1"`
  - Options: `"1:3"`, `"3:1"`, `"1:2"`, `"2:1"`, `"9:16"`, `"16:9"`, `"10:16"`, `"16:10"`, `"2:3"`, `"3:2"`, `"3:4"`, `"4:3"`, `"4:5"`, `"5:4"`, `"1:1"`

- **`rendering_speed`** (`RenderingSpeedEnum`, _optional_):
  The rendering speed to use. Default value: `"BALANCED"`
  - Default: `"BALANCED"`
  - Options: `"TURBO"`, `"BALANCED"`, `"QUALITY"`

- **`num_images`** (`integer`, _optional_):
  Number of images to generate. Default value: `1`
  - Default: `1`
  - Range: `1` to `8`

- **`negative_prompt`** (`string`, _optional_):
  Description of what to exclude from the image. Descriptions in the prompt take precedence over descriptions in the negative prompt. Default value: `""`
  - Default: `""`

- **`expand_prompt`** (`boolean`, _optional_):
  Whether to expand the prompt with MagicPrompt functionality. Default value: `true`
  - Default: `true`

- **`seed`** (`integer`, _optional_):
  Seed for the random number generator.

- **`sync_mode`** (`boolean`, _optional_):
  If `True`, the media will be returned as a data URI and the output data won't be available in the request history.
  - Default: `false`



**Required Parameters Example**:

```json
{
  "model_id": "",
  "prompt": "A photo in my custom style"
}
```

**Full Example**:

```json
{
  "model_id": "",
  "prompt": "A photo in my custom style",
  "aspect_ratio": "1:1",
  "rendering_speed": "BALANCED",
  "num_images": 1,
  "expand_prompt": true
}
```


### Output Schema

The API returns the following output format:

- **`images`** (`list<File>`, _required_):
  The generated images.
  - Array of File
  - Examples: [{"url":"https://v3.fal.media/files/penguin/lHdRabS80guysb8Zw1kul_image.png"}]

- **`seed`** (`integer`, _required_):
  Seed used for the random number generator.
  - Examples: 123456



**Example Response**:

```json
{
  "images": [
    {
      "url": "https://v3.fal.media/files/penguin/lHdRabS80guysb8Zw1kul_image.png"
    }
  ],
  "seed": 123456
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/ideogram/custom-models/generate \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "model_id": "",
     "prompt": "A photo in my custom style"
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
    "fal-ai/ideogram/custom-models/generate",
    arguments={
        "model_id": "",
        "prompt": "A photo in my custom style"
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

const result = await fal.subscribe("fal-ai/ideogram/custom-models/generate", {
  input: {
    model_id: "",
    prompt: "A photo in my custom style"
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

- [Model Playground](https://fal.ai/models/fal-ai/ideogram/custom-models/generate)
- [API Documentation](https://fal.ai/models/fal-ai/ideogram/custom-models/generate/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/ideogram/custom-models/generate)

### fal.ai Platform

- [Platform Documentation](https://docs.fal.ai)
- [Python Client](https://docs.fal.ai/clients/python)
- [JavaScript Client](https://docs.fal.ai/clients/javascript)
