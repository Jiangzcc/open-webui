# Hidream I1 Full

> HiDream-I1 full is a new open-source image generative foundation model with 17B parameters that achieves state-of-the-art image generation quality within seconds.


## Overview

- **Endpoint**: `https://fal.run/fal-ai/hidream-i1-full/image-to-image`
- **Model ID**: `fal-ai/hidream-i1-full/image-to-image`
- **Category**: image-to-image
- **Kind**: inference
**Description**: HiDream-I1 full is a new open-source image generative foundation model with 17B parameters that achieves state-of-the-art image generation quality within seconds.

**Tags**: image-to-image, hidream



## Pricing

- **Price**: $0.05 per megapixels

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _required_):
  The prompt to generate an image from.
  - Examples: "An old man"

- **`negative_prompt`** (`string`, _optional_):
  The negative prompt to use. Use it to address details that you don't want
  in the image. This could be colors, objects, scenery and even the small details
  (e.g. moustache, blurry, low resolution). Default value: `""`
  - Default: `""`
  - Examples: ""

- **`image_size`** (`ImageSize | Enum`, _optional_):
  The size of the generated image. Setting to None uses the input image's size.
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
  the model to stick to your prompt when looking for a related image to show you. Default value: `5`
  - Default: `5`
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

- **`loras`** (`list<LoraWeight>`, _optional_):
  A list of LoRAs to apply to the model. Each LoRA specifies its path, scale, and optional weight name.
  - Default: `[]`
  - Array of LoraWeight

- **`image_url`** (`string`, _required_):
  The image URL to generate an image from.
  - Examples: "https://v3.fal.media/files/tiger/C9qhzoMrg6Sg7lYh_ocrZ_example_man.png"

- **`strength`** (`float`, _optional_):
  Denoising strength for image-to-image generation. Default value: `0.75`
  - Default: `0.75`
  - Range: `0` to `1`



**Required Parameters Example**:

```json
{
  "prompt": "An old man",
  "image_url": "https://v3.fal.media/files/tiger/C9qhzoMrg6Sg7lYh_ocrZ_example_man.png"
}
```

**Full Example**:

```json
{
  "prompt": "An old man",
  "negative_prompt": "",
  "num_inference_steps": 50,
  "guidance_scale": 5,
  "num_images": 1,
  "enable_safety_checker": true,
  "output_format": "jpeg",
  "loras": [],
  "image_url": "https://v3.fal.media/files/tiger/C9qhzoMrg6Sg7lYh_ocrZ_example_man.png",
  "strength": 0.75
}
```


### Output Schema

The API returns the following output format:

- **`images`** (`list<Image>`, _required_):
  The generated images
  - Array of Image
  - Examples: [{"width":1024,"content_type":"image/jpeg","url":"https://v3.fal.media/files/lion/eIyinD1FLsdjjreSZzD6d.jpeg","height":1024}]

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
      "url": "https://v3.fal.media/files/lion/eIyinD1FLsdjjreSZzD6d.jpeg",
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
  --url https://fal.run/fal-ai/hidream-i1-full/image-to-image \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "An old man",
     "image_url": "https://v3.fal.media/files/tiger/C9qhzoMrg6Sg7lYh_ocrZ_example_man.png"
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
    "fal-ai/hidream-i1-full/image-to-image",
    arguments={
        "prompt": "An old man",
        "image_url": "https://v3.fal.media/files/tiger/C9qhzoMrg6Sg7lYh_ocrZ_example_man.png"
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

const result = await fal.subscribe("fal-ai/hidream-i1-full/image-to-image", {
  input: {
    prompt: "An old man",
    image_url: "https://v3.fal.media/files/tiger/C9qhzoMrg6Sg7lYh_ocrZ_example_man.png"
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

- [Model Playground](https://fal.ai/models/fal-ai/hidream-i1-full/image-to-image)
- [API Documentation](https://fal.ai/models/fal-ai/hidream-i1-full/image-to-image/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/hidream-i1-full/image-to-image)

### fal.ai Platform

- [Platform Documentation](https://docs.fal.ai)
- [Python Client](https://docs.fal.ai/clients/python)
- [JavaScript Client](https://docs.fal.ai/clients/javascript)
