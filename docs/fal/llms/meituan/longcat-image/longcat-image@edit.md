# Longcat Image

> LongCat image Edit is a 6B parameter image editing model excelling at multilingual text rendering, photorealism and deployment efficiency.


## Overview

- **Endpoint**: `https://fal.run/fal-ai/longcat-image/edit`
- **Model ID**: `fal-ai/longcat-image/edit`
- **Category**: image-to-image
- **Kind**: inference


## Pricing

- **Price**: $0.15 per megapixels

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _required_):
  The prompt to edit the image with.
  - Examples: "Add the text \"Fal is fast\" in elegant cursive font with lightning streaks at the top of the image."

- **`num_inference_steps`** (`integer`, _optional_):
  The number of inference steps to perform. Default value: `28`
  - Default: `28`
  - Range: `1` to `50`

- **`guidance_scale`** (`float`, _optional_):
  The guidance scale to use for the image generation. Default value: `4.5`
  - Default: `4.5`
  - Range: `1` to `20`

- **`seed`** (`integer`, _optional_):
  The same seed and the same prompt given to the same version of the model
  will output the same image every time.

- **`sync_mode`** (`boolean`, _optional_):
  If `True`, the media will be returned as a data URI and the output data won't be available in the request history.
  - Default: `false`

- **`num_images`** (`integer`, _optional_):
  The number of images to generate. Default value: `1`
  - Default: `1`
  - Range: `1` to `4`

- **`enable_safety_checker`** (`boolean`, _optional_):
  If set to true, the safety checker will be enabled. Default value: `true`
  - Default: `true`

- **`output_format`** (`OutputFormatEnum`, _optional_):
  The format of the generated image. Default value: `"png"`
  - Default: `"png"`
  - Options: `"jpeg"`, `"png"`, `"webp"`

- **`acceleration`** (`AccelerationEnum`, _optional_):
  The acceleration level to use. Default value: `"regular"`
  - Default: `"regular"`
  - Options: `"none"`, `"regular"`, `"high"`

- **`image_url`** (`string`, _required_):
  The URL of the image to edit.
  - Examples: "https://storage.googleapis.com/falserverless/example_inputs/longcat_image/edit_input.png"



**Required Parameters Example**:

```json
{
  "prompt": "Add the text \"Fal is fast\" in elegant cursive font with lightning streaks at the top of the image.",
  "image_url": "https://storage.googleapis.com/falserverless/example_inputs/longcat_image/edit_input.png"
}
```

**Full Example**:

```json
{
  "prompt": "Add the text \"Fal is fast\" in elegant cursive font with lightning streaks at the top of the image.",
  "num_inference_steps": 28,
  "guidance_scale": 4.5,
  "num_images": 1,
  "enable_safety_checker": true,
  "output_format": "png",
  "acceleration": "regular",
  "image_url": "https://storage.googleapis.com/falserverless/example_inputs/longcat_image/edit_input.png"
}
```


### Output Schema

The API returns the following output format:

- **`images`** (`list<Image>`, _required_):
  The generated image files info.
  - Array of Image
  - Examples: [{"height":768,"content_type":"image/png","width":1024,"url":"https://storage.googleapis.com/falserverless/example_outputs/longcat_image/edit.png"}]

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
      "height": 768,
      "content_type": "image/png",
      "width": 1024,
      "url": "https://storage.googleapis.com/falserverless/example_outputs/longcat_image/edit.png"
    }
  ],
  "prompt": ""
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/longcat-image/edit \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "Add the text \"Fal is fast\" in elegant cursive font with lightning streaks at the top of the image.",
     "image_url": "https://storage.googleapis.com/falserverless/example_inputs/longcat_image/edit_input.png"
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
    "fal-ai/longcat-image/edit",
    arguments={
        "prompt": "Add the text \"Fal is fast\" in elegant cursive font with lightning streaks at the top of the image.",
        "image_url": "https://storage.googleapis.com/falserverless/example_inputs/longcat_image/edit_input.png"
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

const result = await fal.subscribe("fal-ai/longcat-image/edit", {
  input: {
    prompt: "Add the text \"Fal is fast\" in elegant cursive font with lightning streaks at the top of the image.",
    image_url: "https://storage.googleapis.com/falserverless/example_inputs/longcat_image/edit_input.png"
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

- [Model Playground](https://fal.ai/models/fal-ai/longcat-image/edit)
- [API Documentation](https://fal.ai/models/fal-ai/longcat-image/edit/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/longcat-image/edit)

### fal.ai Platform

- [Platform Documentation](https://docs.fal.ai)
- [Python Client](https://docs.fal.ai/clients/python)
- [JavaScript Client](https://docs.fal.ai/clients/javascript)
