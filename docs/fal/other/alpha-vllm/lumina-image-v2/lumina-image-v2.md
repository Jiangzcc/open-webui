# Lumina Image 2

> Lumina-Image-2.0 is a 2 billion parameter flow-based diffusion transforer which features improved performance in image quality, typography, complex prompt understanding, and resource-efficiency.


## Overview

- **Endpoint**: `https://fal.run/fal-ai/lumina-image/v2`
- **Model ID**: `fal-ai/lumina-image/v2`
- **Category**: text-to-image
- **Kind**: inference
**Tags**: diffusion, typography, style



## Pricing

- **Price**: $0.075 per megapixels

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _required_):
  The prompt to generate an image from.
  - Examples: "A vibrant and artistic digital composition featuring colorful splashes of paint in the background, creating an energetic and dynamic effect. The text 'Lumina on Fal' is elegantly integrated into the scene, standing out with a modern, bold, and slightly futuristic font. The colors are bright and varied, including neon blues, purples, pinks, and oranges, blending seamlessly in a fluid, abstract style. The text appears slightly illuminated, complementing the vivid splashes around it."

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

- **`system_prompt`** (`string`, _optional_):
  The system prompt to use. Default value: `"You are an assistant designed to generate superior images with the superior degree of image-text alignment based on textual prompts or user prompts."`
  - Default: `"You are an assistant designed to generate superior images with the superior degree of image-text alignment based on textual prompts or user prompts."`

- **`seed`** (`integer`, _optional_):
  The same seed and the same prompt given to the same version of the model
  will output the same image every time.

- **`guidance_scale`** (`float`, _optional_):
  The CFG (Classifier Free Guidance) scale is a measure of how close you want
  the model to stick to your prompt when looking for a related image to show you. Default value: `4`
  - Default: `4`
  - Range: `0` to `20`

- **`num_inference_steps`** (`integer`, _optional_):
  The number of inference steps to perform. Default value: `30`
  - Default: `30`
  - Range: `1` to `50`

- **`cfg_normalization`** (`boolean`, _optional_):
  Whether to apply normalization-based guidance scale. Default value: `true`
  - Default: `true`

- **`cfg_trunc_ratio`** (`float`, _optional_):
  The ratio of the timestep interval to apply normalization-based guidance scale. Default value: `1`
  - Default: `1`
  - Range: `0` to `1`

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
  "prompt": "A vibrant and artistic digital composition featuring colorful splashes of paint in the background, creating an energetic and dynamic effect. The text 'Lumina on Fal' is elegantly integrated into the scene, standing out with a modern, bold, and slightly futuristic font. The colors are bright and varied, including neon blues, purples, pinks, and oranges, blending seamlessly in a fluid, abstract style. The text appears slightly illuminated, complementing the vivid splashes around it."
}
```

**Full Example**:

```json
{
  "prompt": "A vibrant and artistic digital composition featuring colorful splashes of paint in the background, creating an energetic and dynamic effect. The text 'Lumina on Fal' is elegantly integrated into the scene, standing out with a modern, bold, and slightly futuristic font. The colors are bright and varied, including neon blues, purples, pinks, and oranges, blending seamlessly in a fluid, abstract style. The text appears slightly illuminated, complementing the vivid splashes around it.",
  "image_size": "landscape_4_3",
  "negative_prompt": "",
  "system_prompt": "You are an assistant designed to generate superior images with the superior degree of image-text alignment based on textual prompts or user prompts.",
  "guidance_scale": 4,
  "num_inference_steps": 30,
  "cfg_normalization": true,
  "cfg_trunc_ratio": 1,
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
  - Examples: [{"url":"https://v3.fal.media/files/rabbit/pBwaEZysJhnstKWEHGpLc.png","content_type":"image/jpeg","height":768,"width":1024}]

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
      "url": "https://v3.fal.media/files/rabbit/pBwaEZysJhnstKWEHGpLc.png",
      "content_type": "image/jpeg",
      "height": 768,
      "width": 1024
    }
  ],
  "prompt": ""
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/lumina-image/v2 \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "A vibrant and artistic digital composition featuring colorful splashes of paint in the background, creating an energetic and dynamic effect. The text 'Lumina on Fal' is elegantly integrated into the scene, standing out with a modern, bold, and slightly futuristic font. The colors are bright and varied, including neon blues, purples, pinks, and oranges, blending seamlessly in a fluid, abstract style. The text appears slightly illuminated, complementing the vivid splashes around it."
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
    "fal-ai/lumina-image/v2",
    arguments={
        "prompt": "A vibrant and artistic digital composition featuring colorful splashes of paint in the background, creating an energetic and dynamic effect. The text 'Lumina on Fal' is elegantly integrated into the scene, standing out with a modern, bold, and slightly futuristic font. The colors are bright and varied, including neon blues, purples, pinks, and oranges, blending seamlessly in a fluid, abstract style. The text appears slightly illuminated, complementing the vivid splashes around it."
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

const result = await fal.subscribe("fal-ai/lumina-image/v2", {
  input: {
    prompt: "A vibrant and artistic digital composition featuring colorful splashes of paint in the background, creating an energetic and dynamic effect. The text 'Lumina on Fal' is elegantly integrated into the scene, standing out with a modern, bold, and slightly futuristic font. The colors are bright and varied, including neon blues, purples, pinks, and oranges, blending seamlessly in a fluid, abstract style. The text appears slightly illuminated, complementing the vivid splashes around it."
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

- [Model Playground](https://fal.ai/models/fal-ai/lumina-image/v2)
- [API Documentation](https://fal.ai/models/fal-ai/lumina-image/v2/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/lumina-image/v2)

### fal.ai Platform

- [Platform Documentation](https://docs.fal.ai)
- [Python Client](https://docs.fal.ai/clients/python)
- [JavaScript Client](https://docs.fal.ai/clients/javascript)
