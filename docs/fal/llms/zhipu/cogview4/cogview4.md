# CogView

> Generate high quality images from text prompts using CogView4. Longer text prompts will result in better quality images.


## Overview

- **Endpoint**: `https://fal.run/fal-ai/cogview4`
- **Model ID**: `fal-ai/cogview4`
- **Category**: text-to-image
- **Kind**: inference
**Tags**: stylized



## Pricing

- **Price**: $0.1 per megapixels

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _required_):
  The prompt to generate an image from.
  - Examples: "A vibrant and artistic digital composition featuring colorful splashes of paint in the background, creating an energetic and dynamic effect. The text 'CogView4 on Fal' is elegantly integrated into the scene, standing out with a modern, bold, and slightly futuristic font. The colors are bright and varied, including neon blues, purples, pinks, and oranges, blending seamlessly in a fluid, abstract style. The text appears slightly illuminated, complementing the vivid splashes around it."

- **`image_size`** (`ImageSize | Enum`, _optional_):
  The size of the generated image. Default value: `landscape_4_3`
  - Default: `"landscape_4_3"`
  - One of: ImageSize | Enum

- **`negative_prompt`** (`string`, _optional_):
  The negative prompt to use. Use it to address details that you don't want
  in the image. This could be colors, objects, scenery and even the small details
  (e.g. moustache, blurry, low resolution). Default value: `""`
  - Default: `""`
  - Examples: ""

- **`seed`** (`integer`, _optional_):
  The same seed and the same prompt given to the same version of the model
  will output the same image every time.

- **`guidance_scale`** (`float`, _optional_):
  The CFG (Classifier Free Guidance) scale is a measure of how close you want
  the model to stick to your prompt when looking for a related image to show you. Default value: `3.5`
  - Default: `3.5`
  - Range: `0` to `20`

- **`num_inference_steps`** (`integer`, _optional_):
  The number of inference steps to perform. Default value: `50`
  - Default: `50`
  - Range: `1` to `50`

- **`num_images`** (`integer`, _optional_):
  The number of images to generate. Default value: `1`
  - Default: `1`
  - Range: `1` to `4`

- **`sync_mode`** (`boolean`, _optional_):
  If `True`, the media will be returned as a data URI and the output data won't be available in the request history.
  - Default: `false`

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
  "prompt": "A vibrant and artistic digital composition featuring colorful splashes of paint in the background, creating an energetic and dynamic effect. The text 'CogView4 on Fal' is elegantly integrated into the scene, standing out with a modern, bold, and slightly futuristic font. The colors are bright and varied, including neon blues, purples, pinks, and oranges, blending seamlessly in a fluid, abstract style. The text appears slightly illuminated, complementing the vivid splashes around it."
}
```

**Full Example**:

```json
{
  "prompt": "A vibrant and artistic digital composition featuring colorful splashes of paint in the background, creating an energetic and dynamic effect. The text 'CogView4 on Fal' is elegantly integrated into the scene, standing out with a modern, bold, and slightly futuristic font. The colors are bright and varied, including neon blues, purples, pinks, and oranges, blending seamlessly in a fluid, abstract style. The text appears slightly illuminated, complementing the vivid splashes around it.",
  "image_size": "landscape_4_3",
  "negative_prompt": "",
  "guidance_scale": 3.5,
  "num_inference_steps": 50,
  "num_images": 1,
  "enable_safety_checker": true,
  "output_format": "jpeg"
}
```


### Output Schema

The API returns the following output format:

- **`images`** (`list<Image>`, _required_):
  The generated images
  - Array of Image
  - Examples: [{"height":768,"width":1024,"content_type":"image/jpeg","url":"https://v3.fal.media/files/tiger/rN6_PpE-o8QlSecqFku6h.jpeg"}]

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
      "width": 1024,
      "content_type": "image/jpeg",
      "url": "https://v3.fal.media/files/tiger/rN6_PpE-o8QlSecqFku6h.jpeg"
    }
  ],
  "prompt": ""
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/cogview4 \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "A vibrant and artistic digital composition featuring colorful splashes of paint in the background, creating an energetic and dynamic effect. The text 'CogView4 on Fal' is elegantly integrated into the scene, standing out with a modern, bold, and slightly futuristic font. The colors are bright and varied, including neon blues, purples, pinks, and oranges, blending seamlessly in a fluid, abstract style. The text appears slightly illuminated, complementing the vivid splashes around it."
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
    "fal-ai/cogview4",
    arguments={
        "prompt": "A vibrant and artistic digital composition featuring colorful splashes of paint in the background, creating an energetic and dynamic effect. The text 'CogView4 on Fal' is elegantly integrated into the scene, standing out with a modern, bold, and slightly futuristic font. The colors are bright and varied, including neon blues, purples, pinks, and oranges, blending seamlessly in a fluid, abstract style. The text appears slightly illuminated, complementing the vivid splashes around it."
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

const result = await fal.subscribe("fal-ai/cogview4", {
  input: {
    prompt: "A vibrant and artistic digital composition featuring colorful splashes of paint in the background, creating an energetic and dynamic effect. The text 'CogView4 on Fal' is elegantly integrated into the scene, standing out with a modern, bold, and slightly futuristic font. The colors are bright and varied, including neon blues, purples, pinks, and oranges, blending seamlessly in a fluid, abstract style. The text appears slightly illuminated, complementing the vivid splashes around it."
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

- [Model Playground](https://fal.ai/models/fal-ai/cogview4)
- [API Documentation](https://fal.ai/models/fal-ai/cogview4/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/cogview4)

### fal.ai Platform

- [Platform Documentation](https://docs.fal.ai)
- [Python Client](https://docs.fal.ai/clients/python)
- [JavaScript Client](https://docs.fal.ai/clients/javascript)
