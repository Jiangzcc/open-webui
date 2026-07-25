# Z Image Turbo Image To Image

> Generate images from text and images using Z-Image Turbo, Tongyi-MAI's super-fast 6B model.


## Overview

- **Endpoint**: `https://fal.run/fal-ai/z-image/turbo/image-to-image`
- **Model ID**: `fal-ai/z-image/turbo/image-to-image`
- **Category**: image-to-image
- **Kind**: inference
**Tags**: turbo, z-image, fast



## Pricing

- **Price**: $0.005 per megapixels

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _required_):
  The prompt to generate an image from.
  - Examples: "A young Asian woman with long, vibrant purple hair stands on a sunlit sandy beach, posing confidently with her left hand resting on her hip. She gazes directly at the camera with a neutral expression. A sleek black ribbon bow is tied neatly on the right side of her head, just above her ear. She wears a flowing white cotton dress with a fitted bodice and a flared skirt that reaches mid-calf, slightly lifted by a gentle sea breeze. The beach behind her features fine, pale golden sand with subtle footprints, leading to calm turquoise waves under a clear blue sky with soft, wispy clouds. The lighting is natural daylight, casting soft shadows to her left, indicating late afternoon sun. The horizon line is visible in the background, with a faint silhouette of distant dunes. Her skin tone is fair with a natural glow, and her facial features are delicately defined. The composition is centered on her figure, framed from mid-thigh up, with shallow depth of field blurring the distant waves slightly."

- **`image_size`** (`ImageSize | Enum`, _optional_):
  The size of the generated image. Default value: `auto`
  - Default: `"auto"`
  - One of: ImageSize | Enum

- **`num_inference_steps`** (`integer`, _optional_):
  The number of inference steps to perform. Default value: `8`
  - Default: `8`
  - Range: `1` to `8`

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

- **`enable_prompt_expansion`** (`boolean`, _optional_):
  Whether to enable prompt expansion. Note: this will increase the price by 0.0025 credits per request.
  - Default: `false`

- **`image_url`** (`string`, _required_):
  URL of Image for Image-to-Image generation.
  - Examples: "https://storage.googleapis.com/falserverless/example_inputs/z-image-turbo-i2i-input.png"

- **`strength`** (`float`, _optional_):
  The strength of the image-to-image conditioning. Default value: `0.6`
  - Default: `0.6`



**Required Parameters Example**:

```json
{
  "prompt": "A young Asian woman with long, vibrant purple hair stands on a sunlit sandy beach, posing confidently with her left hand resting on her hip. She gazes directly at the camera with a neutral expression. A sleek black ribbon bow is tied neatly on the right side of her head, just above her ear. She wears a flowing white cotton dress with a fitted bodice and a flared skirt that reaches mid-calf, slightly lifted by a gentle sea breeze. The beach behind her features fine, pale golden sand with subtle footprints, leading to calm turquoise waves under a clear blue sky with soft, wispy clouds. The lighting is natural daylight, casting soft shadows to her left, indicating late afternoon sun. The horizon line is visible in the background, with a faint silhouette of distant dunes. Her skin tone is fair with a natural glow, and her facial features are delicately defined. The composition is centered on her figure, framed from mid-thigh up, with shallow depth of field blurring the distant waves slightly.",
  "image_url": "https://storage.googleapis.com/falserverless/example_inputs/z-image-turbo-i2i-input.png"
}
```

**Full Example**:

```json
{
  "prompt": "A young Asian woman with long, vibrant purple hair stands on a sunlit sandy beach, posing confidently with her left hand resting on her hip. She gazes directly at the camera with a neutral expression. A sleek black ribbon bow is tied neatly on the right side of her head, just above her ear. She wears a flowing white cotton dress with a fitted bodice and a flared skirt that reaches mid-calf, slightly lifted by a gentle sea breeze. The beach behind her features fine, pale golden sand with subtle footprints, leading to calm turquoise waves under a clear blue sky with soft, wispy clouds. The lighting is natural daylight, casting soft shadows to her left, indicating late afternoon sun. The horizon line is visible in the background, with a faint silhouette of distant dunes. Her skin tone is fair with a natural glow, and her facial features are delicately defined. The composition is centered on her figure, framed from mid-thigh up, with shallow depth of field blurring the distant waves slightly.",
  "image_size": "auto",
  "num_inference_steps": 8,
  "num_images": 1,
  "enable_safety_checker": true,
  "output_format": "png",
  "acceleration": "regular",
  "image_url": "https://storage.googleapis.com/falserverless/example_inputs/z-image-turbo-i2i-input.png",
  "strength": 0.6
}
```


### Output Schema

The API returns the following output format:

- **`images`** (`list<ImageFile>`, _required_):
  The generated image files info.
  - Array of ImageFile
  - Examples: [{"url":"https://storage.googleapis.com/falserverless/example_outputs/z-image-turbo-i2i-output.png","height":1728,"content_type":"image/png","width":992}]

- **`timings`** (`Timings`, _required_):
  The timings of the generation process.

- **`seed`** (`integer`, _required_):
  Seed of the generated Image. It will be the same value of the one passed in the input or the randomly generated that was used in case none was passed.

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
      "url": "https://storage.googleapis.com/falserverless/example_outputs/z-image-turbo-i2i-output.png",
      "height": 1728,
      "content_type": "image/png",
      "width": 992
    }
  ],
  "prompt": ""
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/z-image/turbo/image-to-image \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "A young Asian woman with long, vibrant purple hair stands on a sunlit sandy beach, posing confidently with her left hand resting on her hip. She gazes directly at the camera with a neutral expression. A sleek black ribbon bow is tied neatly on the right side of her head, just above her ear. She wears a flowing white cotton dress with a fitted bodice and a flared skirt that reaches mid-calf, slightly lifted by a gentle sea breeze. The beach behind her features fine, pale golden sand with subtle footprints, leading to calm turquoise waves under a clear blue sky with soft, wispy clouds. The lighting is natural daylight, casting soft shadows to her left, indicating late afternoon sun. The horizon line is visible in the background, with a faint silhouette of distant dunes. Her skin tone is fair with a natural glow, and her facial features are delicately defined. The composition is centered on her figure, framed from mid-thigh up, with shallow depth of field blurring the distant waves slightly.",
     "image_url": "https://storage.googleapis.com/falserverless/example_inputs/z-image-turbo-i2i-input.png"
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
    "fal-ai/z-image/turbo/image-to-image",
    arguments={
        "prompt": "A young Asian woman with long, vibrant purple hair stands on a sunlit sandy beach, posing confidently with her left hand resting on her hip. She gazes directly at the camera with a neutral expression. A sleek black ribbon bow is tied neatly on the right side of her head, just above her ear. She wears a flowing white cotton dress with a fitted bodice and a flared skirt that reaches mid-calf, slightly lifted by a gentle sea breeze. The beach behind her features fine, pale golden sand with subtle footprints, leading to calm turquoise waves under a clear blue sky with soft, wispy clouds. The lighting is natural daylight, casting soft shadows to her left, indicating late afternoon sun. The horizon line is visible in the background, with a faint silhouette of distant dunes. Her skin tone is fair with a natural glow, and her facial features are delicately defined. The composition is centered on her figure, framed from mid-thigh up, with shallow depth of field blurring the distant waves slightly.",
        "image_url": "https://storage.googleapis.com/falserverless/example_inputs/z-image-turbo-i2i-input.png"
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

const result = await fal.subscribe("fal-ai/z-image/turbo/image-to-image", {
  input: {
    prompt: "A young Asian woman with long, vibrant purple hair stands on a sunlit sandy beach, posing confidently with her left hand resting on her hip. She gazes directly at the camera with a neutral expression. A sleek black ribbon bow is tied neatly on the right side of her head, just above her ear. She wears a flowing white cotton dress with a fitted bodice and a flared skirt that reaches mid-calf, slightly lifted by a gentle sea breeze. The beach behind her features fine, pale golden sand with subtle footprints, leading to calm turquoise waves under a clear blue sky with soft, wispy clouds. The lighting is natural daylight, casting soft shadows to her left, indicating late afternoon sun. The horizon line is visible in the background, with a faint silhouette of distant dunes. Her skin tone is fair with a natural glow, and her facial features are delicately defined. The composition is centered on her figure, framed from mid-thigh up, with shallow depth of field blurring the distant waves slightly.",
    image_url: "https://storage.googleapis.com/falserverless/example_inputs/z-image-turbo-i2i-input.png"
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

- [Model Playground](https://fal.ai/models/fal-ai/z-image/turbo/image-to-image)
- [API Documentation](https://fal.ai/models/fal-ai/z-image/turbo/image-to-image/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/z-image/turbo/image-to-image)

### fal.ai Platform

- [Platform Documentation](https://docs.fal.ai)
- [Python Client](https://docs.fal.ai/clients/python)
- [JavaScript Client](https://docs.fal.ai/clients/javascript)
