# OmniGen v1

> OmniGen is a unified image generation model that can generate a wide range of images from multi-modal prompts. It can be used for various tasks such as Image Editing, Personalized Image Generation, Virtual Try-On, Multi Person Generation and more!


## Overview

- **Endpoint**: `https://fal.run/fal-ai/omnigen-v1`
- **Model ID**: `fal-ai/omnigen-v1`
- **Category**: text-to-image
- **Kind**: inference
**Tags**: multimodal, editing, try-on



## Pricing

- **Price**: $0.1 per processed megapixels

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _required_):
  The prompt to generate an image from.
  - Examples: "Neon words \"Omni Gen\" are flashing in the prosperous future city, the sense of science and technology, quality details, hyper realistic, high definition, 8K, photo, best quality, high quality."

- **`input_image_urls`** (`list<string>`, _optional_):
  URL of images to use while generating the image, Use <img><|image_1|></img> for the first image and so on.
  - Default: `[]`
  - Array of string

- **`image_size`** (`ImageSize | Enum`, _optional_):
  The size of the generated image. Default value: `square_hd`
  - Default: `"square_hd"`
  - One of: ImageSize | Enum

- **`num_inference_steps`** (`integer`, _optional_):
  The number of inference steps to perform. Default value: `50`
  - Default: `50`
  - Range: `1` to `50`

- **`seed`** (`integer`, _optional_):
  The same seed and the same prompt given to the same version of the model
  will output the same image every time.

- **`guidance_scale`** (`float`, _optional_):
  The CFG (Classifier Free Guidance) scale is a measure of how close you want
  the model to stick to your prompt when looking for a related image to show you. Default value: `3`
  - Default: `3`
  - Range: `0` to `20`

- **`img_guidance_scale`** (`float`, _optional_):
  The Image Guidance scale is a measure of how close you want
  the model to stick to your input image when looking for a related image to show you. Default value: `1.6`
  - Default: `1.6`
  - Range: `0` to `20`

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
  The format of the generated image. Default value: `"jpeg"`
  - Default: `"jpeg"`
  - Options: `"jpeg"`, `"png"`



**Required Parameters Example**:

```json
{
  "prompt": "Neon words \"Omni Gen\" are flashing in the prosperous future city, the sense of science and technology, quality details, hyper realistic, high definition, 8K, photo, best quality, high quality."
}
```

**Full Example**:

```json
{
  "prompt": "Neon words \"Omni Gen\" are flashing in the prosperous future city, the sense of science and technology, quality details, hyper realistic, high definition, 8K, photo, best quality, high quality.",
  "image_size": "square_hd",
  "num_inference_steps": 50,
  "guidance_scale": 3,
  "img_guidance_scale": 1.6,
  "num_images": 1,
  "enable_safety_checker": true,
  "output_format": "jpeg"
}
```


### Output Schema

The API returns the following output format:

- **`images`** (`list<Image>`, _required_):
  The generated image files info.
  - Array of Image

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
      "url": "",
      "content_type": "image/jpeg"
    }
  ],
  "prompt": ""
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/omnigen-v1 \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "Neon words \"Omni Gen\" are flashing in the prosperous future city, the sense of science and technology, quality details, hyper realistic, high definition, 8K, photo, best quality, high quality."
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
    "fal-ai/omnigen-v1",
    arguments={
        "prompt": "Neon words \"Omni Gen\" are flashing in the prosperous future city, the sense of science and technology, quality details, hyper realistic, high definition, 8K, photo, best quality, high quality."
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

const result = await fal.subscribe("fal-ai/omnigen-v1", {
  input: {
    prompt: "Neon words \"Omni Gen\" are flashing in the prosperous future city, the sense of science and technology, quality details, hyper realistic, high definition, 8K, photo, best quality, high quality."
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

- [Model Playground](https://fal.ai/models/fal-ai/omnigen-v1)
- [API Documentation](https://fal.ai/models/fal-ai/omnigen-v1/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/omnigen-v1)

### fal.ai Platform

- [Platform Documentation](https://docs.fal.ai)
- [Python Client](https://docs.fal.ai/clients/python)
- [JavaScript Client](https://docs.fal.ai/clients/javascript)
