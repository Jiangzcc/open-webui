# Reve 2.1

> Generate high-quality images from text prompts with strong prompt adherence, layout intelligence, and accurate text rendering using Reve 2.1.


## Overview

- **Endpoint**: `https://fal.run/reve/2.1/text-to-image`
- **Model ID**: `reve/2.1/text-to-image`
- **Category**: text-to-image
- **Kind**: inference
**Tags**: text-to-image



## Pricing

- **Price**: $0.25 per images

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _required_):
  The text description of the desired image.
  - Examples: "A towering stack of golden fluffy pancakes drizzled with amber honey syrup, topped with fresh blackberries and sliced bananas, served on a white ceramic plate on a rustic wooden table with a soft blue-gray background."

- **`aspect_ratio`** (`AspectRatioEnum`, _optional_):
  The desired aspect ratio of the generated image. With `auto`, the model picks an appropriate aspect ratio for the request. Default value: `"auto"`
  - Default: `"auto"`
  - Options: `"4:1"`, `"3:1"`, `"21:9"`, `"2:1"`, `"17:9"`, `"16:9"`, `"3:2"`, `"4:3"`, `"5:4"`, `"1:1"`, `"4:5"`, `"3:4"`, `"2:3"`, `"9:16"`, `"1:2"`, `"1:3"`, `"1:4"`, `"auto"`
  - Examples: "16:9"

- **`num_images`** (`integer`, _optional_):
  Number of images to generate Default value: `1`
  - Default: `1`
  - Range: `1` to `4`
  - Examples: 1

- **`output_format`** (`OutputFormatEnum`, _optional_):
  Output format for the generated image. Default value: `"png"`
  - Default: `"png"`
  - Options: `"png"`, `"jpeg"`, `"webp"`
  - Examples: "png"

- **`sync_mode`** (`boolean`, _optional_):
  If `True`, the media will be returned as a data URI and the output data won't be available in the request history.
  - Default: `false`



**Required Parameters Example**:

```json
{
  "prompt": "A towering stack of golden fluffy pancakes drizzled with amber honey syrup, topped with fresh blackberries and sliced bananas, served on a white ceramic plate on a rustic wooden table with a soft blue-gray background."
}
```

**Full Example**:

```json
{
  "prompt": "A towering stack of golden fluffy pancakes drizzled with amber honey syrup, topped with fresh blackberries and sliced bananas, served on a white ceramic plate on a rustic wooden table with a soft blue-gray background.",
  "aspect_ratio": "16:9",
  "num_images": 1,
  "output_format": "png"
}
```


### Output Schema

The API returns the following output format:

- **`images`** (`list<Image>`, _required_):
  The generated images
  - Array of Image
  - Examples: [{"url":"https://v3b.fal.media/files/b/panda/-WnGcaJCtfrT6Q2oms97E.png"}]



**Example Response**:

```json
{
  "images": [
    {
      "url": "https://v3b.fal.media/files/b/panda/-WnGcaJCtfrT6Q2oms97E.png"
    }
  ]
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/reve/2.1/text-to-image \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "A towering stack of golden fluffy pancakes drizzled with amber honey syrup, topped with fresh blackberries and sliced bananas, served on a white ceramic plate on a rustic wooden table with a soft blue-gray background."
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
    "reve/2.1/text-to-image",
    arguments={
        "prompt": "A towering stack of golden fluffy pancakes drizzled with amber honey syrup, topped with fresh blackberries and sliced bananas, served on a white ceramic plate on a rustic wooden table with a soft blue-gray background."
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

const result = await fal.subscribe("reve/2.1/text-to-image", {
  input: {
    prompt: "A towering stack of golden fluffy pancakes drizzled with amber honey syrup, topped with fresh blackberries and sliced bananas, served on a white ceramic plate on a rustic wooden table with a soft blue-gray background."
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

- [Model Playground](https://fal.ai/models/reve/2.1/text-to-image)
- [API Documentation](https://fal.ai/models/reve/2.1/text-to-image/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=reve/2.1/text-to-image)

### fal.ai Platform

- [Platform Documentation](https://docs.fal.ai)
- [Python Client](https://docs.fal.ai/clients/python)
- [JavaScript Client](https://docs.fal.ai/clients/javascript)
