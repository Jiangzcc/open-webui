# Juggernaut Flux Pro

> Juggernaut Pro Flux by RunDiffusion is the flagship Juggernaut model rivaling some of the most advanced image models available, often surpassing them in realism. It combines Juggernaut Base with RunDiffusion Photo and features enhancements like reduced background blurriness.


## Overview

- **Endpoint**: `https://fal.run/rundiffusion-fal/juggernaut-flux/pro/image-to-image`
- **Model ID**: `rundiffusion-fal/juggernaut-flux/pro/image-to-image`
- **Category**: image-to-image
- **Kind**: inference
**Tags**: image generation



## Pricing

- **Price**: $0.055 per megapixels

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`image_url`** (`string`, _required_):
  The URL of the image to generate an image from.
  - Examples: "https://fal.media/files/koala/Chls9L2ZnvuipUTEwlnJC.png"

- **`prompt`** (`string`, _required_):
  The prompt to generate an image from.
  - Examples: "a cat dressed as a wizard with a background of a mystic forest."

- **`strength`** (`float`, _optional_):
  The strength of the initial image. Higher strength values are better for this model. Default value: `0.95`
  - Default: `0.95`
  - Range: `0.01` to `1`

- **`num_inference_steps`** (`integer`, _optional_):
  The number of inference steps to perform. Default value: `40`
  - Default: `40`
  - Range: `10` to `50`

- **`seed`** (`integer`, _optional_):
  The same seed and the same prompt given to the same version of the model
  will output the same image every time.

- **`guidance_scale`** (`float`, _optional_):
  The CFG (Classifier Free Guidance) scale is a measure of how close you want
  the model to stick to your prompt when looking for a related image to show you. Default value: `3.5`
  - Default: `3.5`
  - Range: `1` to `20`

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
  - Options: `"jpeg"`, `"png"`



**Required Parameters Example**:

```json
{
  "image_url": "https://fal.media/files/koala/Chls9L2ZnvuipUTEwlnJC.png",
  "prompt": "a cat dressed as a wizard with a background of a mystic forest."
}
```

**Full Example**:

```json
{
  "image_url": "https://fal.media/files/koala/Chls9L2ZnvuipUTEwlnJC.png",
  "prompt": "a cat dressed as a wizard with a background of a mystic forest.",
  "strength": 0.95,
  "num_inference_steps": 40,
  "guidance_scale": 3.5,
  "num_images": 1,
  "enable_safety_checker": true,
  "output_format": "png"
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
  --url https://fal.run/rundiffusion-fal/juggernaut-flux/pro/image-to-image \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "image_url": "https://fal.media/files/koala/Chls9L2ZnvuipUTEwlnJC.png",
     "prompt": "a cat dressed as a wizard with a background of a mystic forest."
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
    "rundiffusion-fal/juggernaut-flux/pro/image-to-image",
    arguments={
        "image_url": "https://fal.media/files/koala/Chls9L2ZnvuipUTEwlnJC.png",
        "prompt": "a cat dressed as a wizard with a background of a mystic forest."
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

const result = await fal.subscribe("rundiffusion-fal/juggernaut-flux/pro/image-to-image", {
  input: {
    image_url: "https://fal.media/files/koala/Chls9L2ZnvuipUTEwlnJC.png",
    prompt: "a cat dressed as a wizard with a background of a mystic forest."
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

- [Model Playground](https://fal.ai/models/rundiffusion-fal/juggernaut-flux/pro/image-to-image)
- [API Documentation](https://fal.ai/models/rundiffusion-fal/juggernaut-flux/pro/image-to-image/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=rundiffusion-fal/juggernaut-flux/pro/image-to-image)

### fal.ai Platform

- [Platform Documentation](https://docs.fal.ai)
- [Python Client](https://docs.fal.ai/clients/python)
- [JavaScript Client](https://docs.fal.ai/clients/javascript)
