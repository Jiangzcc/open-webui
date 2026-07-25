# Flux 2 Lora Gallery

> Transforms images into comic book style


## Overview

- **Endpoint**: `https://fal.run/fal-ai/flux-2-lora-gallery/digital-comic-art`
- **Model ID**: `fal-ai/flux-2-lora-gallery/digital-comic-art`
- **Category**: text-to-image
- **Kind**: inference
**Tags**: stylized, transform



## Pricing

- **Price**: $0.021 per megapixels

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _required_):
  The prompt to generate a digital comic art style image. Use 'd1g1t4l' trigger word for best results.
  - Examples: "A superhero flying over a city, d1g1t4l comic art style", "Action scene with explosion effects, digital comic illustration", "Comic book panel with dramatic lighting"

- **`image_size`** (`ImageSize | Enum`, _optional_):
  The size of the generated image. Default value: `landscape_4_3`
  - Default: `"landscape_4_3"`
  - One of: ImageSize | Enum

- **`guidance_scale`** (`float`, _optional_):
  The CFG (Classifier Free Guidance) scale. Controls how closely the model follows the prompt. Default value: `2.5`
  - Default: `2.5`
  - Range: `0` to `20`

- **`num_inference_steps`** (`integer`, _optional_):
  The number of inference steps to perform. Default value: `40`
  - Default: `40`
  - Range: `4` to `50`

- **`acceleration`** (`AccelerationEnum`, _optional_):
  Acceleration level for image generation. 'regular' balances speed and quality. Default value: `"regular"`
  - Default: `"regular"`
  - Options: `"none"`, `"regular"`

- **`seed`** (`integer`, _optional_):
  Random seed for reproducibility. Same seed with same prompt will produce same result.

- **`sync_mode`** (`boolean`, _optional_):
  If `True`, the media will be returned as a data URI and won't be saved in history.
  - Default: `false`

- **`enable_safety_checker`** (`boolean`, _optional_):
  Whether to enable the safety checker for the generated image. Default value: `true`
  - Default: `true`

- **`output_format`** (`OutputFormatEnum`, _optional_):
  The format of the output image Default value: `"png"`
  - Default: `"png"`
  - Options: `"png"`, `"jpeg"`, `"webp"`

- **`num_images`** (`integer`, _optional_):
  Number of images to generate Default value: `1`
  - Default: `1`
  - Range: `1` to `4`

- **`lora_scale`** (`float`, _optional_):
  The strength of the digital comic art effect. Default value: `1`
  - Default: `1`
  - Range: `0` to `2`



**Required Parameters Example**:

```json
{
  "prompt": "A superhero flying over a city, d1g1t4l comic art style"
}
```

**Full Example**:

```json
{
  "prompt": "A superhero flying over a city, d1g1t4l comic art style",
  "image_size": "landscape_4_3",
  "guidance_scale": 2.5,
  "num_inference_steps": 40,
  "acceleration": "regular",
  "enable_safety_checker": true,
  "output_format": "png",
  "num_images": 1,
  "lora_scale": 1
}
```


### Output Schema

The API returns the following output format:

- **`images`** (`list<Image>`, _required_):
  The generated digital comic art style images
  - Array of Image
  - Examples: [{"url":"https://v3b.fal.media/files/b/tiger/9_onjLEABvvZl9r-R6w_w.png"}]

- **`seed`** (`integer`, _required_):
  The seed used for generation

- **`prompt`** (`string`, _required_):
  The prompt used for generation



**Example Response**:

```json
{
  "images": [
    {
      "url": "https://v3b.fal.media/files/b/tiger/9_onjLEABvvZl9r-R6w_w.png"
    }
  ],
  "prompt": ""
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/flux-2-lora-gallery/digital-comic-art \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "A superhero flying over a city, d1g1t4l comic art style"
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
    "fal-ai/flux-2-lora-gallery/digital-comic-art",
    arguments={
        "prompt": "A superhero flying over a city, d1g1t4l comic art style"
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

const result = await fal.subscribe("fal-ai/flux-2-lora-gallery/digital-comic-art", {
  input: {
    prompt: "A superhero flying over a city, d1g1t4l comic art style"
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

- [Model Playground](https://fal.ai/models/fal-ai/flux-2-lora-gallery/digital-comic-art)
- [API Documentation](https://fal.ai/models/fal-ai/flux-2-lora-gallery/digital-comic-art/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/flux-2-lora-gallery/digital-comic-art)

### fal.ai Platform

- [Platform Documentation](https://docs.fal.ai)
- [Python Client](https://docs.fal.ai/clients/python)
- [JavaScript Client](https://docs.fal.ai/clients/javascript)
