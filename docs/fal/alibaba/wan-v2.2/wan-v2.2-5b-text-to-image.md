# Wan

> Wan 2.2's 5B model generates high-resolution, photorealistic images with powerful prompt understanding and fine-grained visual detail


## Overview

- **Endpoint**: `https://fal.run/fal-ai/wan/v2.2-5b/text-to-image`
- **Model ID**: `fal-ai/wan/v2.2-5b/text-to-image`
- **Category**: text-to-image
- **Kind**: inference


## Pricing

- **Price**: $0.016 per images

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _required_):
  The text prompt to guide image generation.
  - Examples: "In this breathtaking wildlife documentary, we are drawn into an intimate close-up of a majestic lion's face, framed against the backdrop of a vast African savannah at dawn. The camera captures the raw power and nobility of the creature as it gazes intently into the distance, its golden-brown fur glistening under the soft, diffused light that bathes the scene in an ethereal glow. Harsh shadows dance across its features, accentuating the deep wrinkles around its eyes and the rugged texture of its fur, each strand a testament to its age and wisdom. The static camera angle invites viewers to immerse themselves in this moment of profound stillness, where the lion's intense focus hints at an unseen presence or a distant threat. As the sun ascends, the landscape transforms into a symphony of warm hues, enhancing the serene yet tense atmosphere that envelops this extraordinary encounter with nature's untamed beauty."

- **`negative_prompt`** (`string`, _optional_):
  Negative prompt for video generation. Default value: `""`
  - Default: `""`

- **`seed`** (`integer`, _optional_):
  Random seed for reproducibility. If None, a random seed is chosen.

- **`num_inference_steps`** (`integer`, _optional_):
  Number of inference steps for sampling. Higher values give better quality but take longer. Default value: `40`
  - Default: `40`
  - Range: `2` to `50`
  - Examples: 40

- **`enable_safety_checker`** (`boolean`, _optional_):
  If set to true, input data will be checked for safety before processing.
  - Default: `false`
  - Examples: true

- **`enable_output_safety_checker`** (`boolean`, _optional_):
  If set to true, output video will be checked for safety after generation.
  - Default: `false`
  - Examples: false

- **`enable_prompt_expansion`** (`boolean`, _optional_):
  Whether to enable prompt expansion. This will use a large language model to expand the prompt with additional details while maintaining the original meaning.
  - Default: `false`
  - Examples: false

- **`guidance_scale`** (`float`, _optional_):
  Classifier-free guidance scale. Higher values give better adherence to the prompt but may decrease quality. Default value: `3.5`
  - Default: `3.5`
  - Range: `1` to `10`
  - Examples: 3.5

- **`shift`** (`float`, _optional_):
  Shift value for the image. Must be between 1.0 and 10.0. Default value: `2`
  - Default: `2`
  - Range: `1` to `10`
  - Examples: 2

- **`image_size`** (`ImageSize | Enum`, _optional_):
  The size of the generated image. Default value: `square_hd`
  - Default: `"square_hd"`
  - One of: ImageSize | Enum
  - Examples: "square_hd"

- **`image_format`** (`ImageFormatEnum`, _optional_):
  The format of the output image. Default value: `"jpeg"`
  - Default: `"jpeg"`
  - Options: `"png"`, `"jpeg"`
  - Examples: "jpeg"



**Required Parameters Example**:

```json
{
  "prompt": "In this breathtaking wildlife documentary, we are drawn into an intimate close-up of a majestic lion's face, framed against the backdrop of a vast African savannah at dawn. The camera captures the raw power and nobility of the creature as it gazes intently into the distance, its golden-brown fur glistening under the soft, diffused light that bathes the scene in an ethereal glow. Harsh shadows dance across its features, accentuating the deep wrinkles around its eyes and the rugged texture of its fur, each strand a testament to its age and wisdom. The static camera angle invites viewers to immerse themselves in this moment of profound stillness, where the lion's intense focus hints at an unseen presence or a distant threat. As the sun ascends, the landscape transforms into a symphony of warm hues, enhancing the serene yet tense atmosphere that envelops this extraordinary encounter with nature's untamed beauty."
}
```

**Full Example**:

```json
{
  "prompt": "In this breathtaking wildlife documentary, we are drawn into an intimate close-up of a majestic lion's face, framed against the backdrop of a vast African savannah at dawn. The camera captures the raw power and nobility of the creature as it gazes intently into the distance, its golden-brown fur glistening under the soft, diffused light that bathes the scene in an ethereal glow. Harsh shadows dance across its features, accentuating the deep wrinkles around its eyes and the rugged texture of its fur, each strand a testament to its age and wisdom. The static camera angle invites viewers to immerse themselves in this moment of profound stillness, where the lion's intense focus hints at an unseen presence or a distant threat. As the sun ascends, the landscape transforms into a symphony of warm hues, enhancing the serene yet tense atmosphere that envelops this extraordinary encounter with nature's untamed beauty.",
  "num_inference_steps": 40,
  "enable_safety_checker": true,
  "enable_output_safety_checker": false,
  "enable_prompt_expansion": false,
  "guidance_scale": 3.5,
  "shift": 2,
  "image_size": "square_hd",
  "image_format": "jpeg"
}
```


### Output Schema

The API returns the following output format:

- **`image`** (`File`, _required_):
  The generated image file.
  - Examples: {"url":"https://storage.googleapis.com/falserverless/example_outputs/wan/small-t2i-output-2.png"}

- **`seed`** (`integer`, _required_):
  The seed used for generation.



**Example Response**:

```json
{
  "image": {
    "url": "https://storage.googleapis.com/falserverless/example_outputs/wan/small-t2i-output-2.png"
  }
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/wan/v2.2-5b/text-to-image \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "In this breathtaking wildlife documentary, we are drawn into an intimate close-up of a majestic lion's face, framed against the backdrop of a vast African savannah at dawn. The camera captures the raw power and nobility of the creature as it gazes intently into the distance, its golden-brown fur glistening under the soft, diffused light that bathes the scene in an ethereal glow. Harsh shadows dance across its features, accentuating the deep wrinkles around its eyes and the rugged texture of its fur, each strand a testament to its age and wisdom. The static camera angle invites viewers to immerse themselves in this moment of profound stillness, where the lion's intense focus hints at an unseen presence or a distant threat. As the sun ascends, the landscape transforms into a symphony of warm hues, enhancing the serene yet tense atmosphere that envelops this extraordinary encounter with nature's untamed beauty."
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
    "fal-ai/wan/v2.2-5b/text-to-image",
    arguments={
        "prompt": "In this breathtaking wildlife documentary, we are drawn into an intimate close-up of a majestic lion's face, framed against the backdrop of a vast African savannah at dawn. The camera captures the raw power and nobility of the creature as it gazes intently into the distance, its golden-brown fur glistening under the soft, diffused light that bathes the scene in an ethereal glow. Harsh shadows dance across its features, accentuating the deep wrinkles around its eyes and the rugged texture of its fur, each strand a testament to its age and wisdom. The static camera angle invites viewers to immerse themselves in this moment of profound stillness, where the lion's intense focus hints at an unseen presence or a distant threat. As the sun ascends, the landscape transforms into a symphony of warm hues, enhancing the serene yet tense atmosphere that envelops this extraordinary encounter with nature's untamed beauty."
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

const result = await fal.subscribe("fal-ai/wan/v2.2-5b/text-to-image", {
  input: {
    prompt: "In this breathtaking wildlife documentary, we are drawn into an intimate close-up of a majestic lion's face, framed against the backdrop of a vast African savannah at dawn. The camera captures the raw power and nobility of the creature as it gazes intently into the distance, its golden-brown fur glistening under the soft, diffused light that bathes the scene in an ethereal glow. Harsh shadows dance across its features, accentuating the deep wrinkles around its eyes and the rugged texture of its fur, each strand a testament to its age and wisdom. The static camera angle invites viewers to immerse themselves in this moment of profound stillness, where the lion's intense focus hints at an unseen presence or a distant threat. As the sun ascends, the landscape transforms into a symphony of warm hues, enhancing the serene yet tense atmosphere that envelops this extraordinary encounter with nature's untamed beauty."
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

- [Model Playground](https://fal.ai/models/fal-ai/wan/v2.2-5b/text-to-image)
- [API Documentation](https://fal.ai/models/fal-ai/wan/v2.2-5b/text-to-image/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/wan/v2.2-5b/text-to-image)

### fal.ai Platform

- [Platform Documentation](https://docs.fal.ai)
- [Python Client](https://docs.fal.ai/clients/python)
- [JavaScript Client](https://docs.fal.ai/clients/javascript)
