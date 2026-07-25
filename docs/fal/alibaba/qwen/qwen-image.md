# Qwen Image

> Qwen-Image is an image generation foundation model in the Qwen series that achieves significant advances in complex text rendering and precise image editing. 


## Overview

- **Endpoint**: `https://fal.run/fal-ai/qwen-image`
- **Model ID**: `fal-ai/qwen-image`
- **Category**: text-to-image
- **Kind**: inference
**Tags**: text-to-image



## Pricing

- **Price**: $0.02 per megapixels

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _required_):
  The prompt to generate the image with
  - Examples: "Mount Fuji with cherry blossoms in the foreground, clear sky, peaceful spring day, soft natural light, realistic landscape."

- **`image_size`** (`ImageSize | Enum`, _optional_):
  The size of the generated image. Default value: `landscape_4_3`
  - Default: `"landscape_4_3"`
  - One of: ImageSize | Enum

- **`num_inference_steps`** (`integer`, _optional_):
  The number of inference steps to perform. Default value: `30`
  - Default: `30`
  - Range: `2` to `250`

- **`seed`** (`integer`, _optional_):
  The same seed and the same prompt given to the same version of the model
  will output the same image every time.

- **`guidance_scale`** (`float`, _optional_):
  The CFG (Classifier Free Guidance) scale is a measure of how close you want
  the model to stick to your prompt when looking for a related image to show you. Default value: `2.5`
  - Default: `2.5`
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
  The format of the generated image. Default value: `"png"`
  - Default: `"png"`
  - Options: `"jpeg"`, `"png"`

- **`negative_prompt`** (`string`, _optional_):
  The negative prompt for the generation Default value: `" "`
  - Default: `" "`
  - Examples: "blurry, ugly"

- **`acceleration`** (`AccelerationEnum`, _optional_):
  Acceleration level for image generation. Options: 'none', 'regular', 'high'. Higher acceleration increases speed. 'regular' balances speed and quality. 'high' is recommended for images without text. Default value: `"none"`
  - Default: `"none"`
  - Options: `"none"`, `"regular"`, `"high"`
  - Examples: "none"

- **`loras`** (`list<LoraWeight>`, _optional_):
  The LoRAs to use for the image generation. You can use up to 3 LoRAs
  and they will be merged together to generate the final image.
  - Default: `[]`
  - Array of LoraWeight

- **`use_turbo`** (`boolean`, _optional_):
  Enable turbo mode for faster generation with high quality. When enabled, uses optimized settings (10 steps, CFG=1.2).
  - Default: `false`
  - Examples: true



**Required Parameters Example**:

```json
{
  "prompt": "Mount Fuji with cherry blossoms in the foreground, clear sky, peaceful spring day, soft natural light, realistic landscape."
}
```

**Full Example**:

```json
{
  "prompt": "Mount Fuji with cherry blossoms in the foreground, clear sky, peaceful spring day, soft natural light, realistic landscape.",
  "image_size": "landscape_4_3",
  "num_inference_steps": 30,
  "guidance_scale": 2.5,
  "num_images": 1,
  "enable_safety_checker": true,
  "output_format": "png",
  "negative_prompt": "blurry, ugly",
  "acceleration": "none",
  "use_turbo": true
}
```


### Output Schema

The API returns the following output format:

- **`images`** (`list<Image>`, _required_):
  The generated image files info.
  - Array of Image
  - Examples: [{"height":768,"content_type":"image/jpeg","width":1024,"url":"https://v3.fal.media/files/rabbit/KoIbq6nhDBDPxDQrivW-m.png"}]

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
      "content_type": "image/jpeg",
      "width": 1024,
      "url": "https://v3.fal.media/files/rabbit/KoIbq6nhDBDPxDQrivW-m.png"
    }
  ],
  "prompt": ""
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/qwen-image \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "Mount Fuji with cherry blossoms in the foreground, clear sky, peaceful spring day, soft natural light, realistic landscape."
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
    "fal-ai/qwen-image",
    arguments={
        "prompt": "Mount Fuji with cherry blossoms in the foreground, clear sky, peaceful spring day, soft natural light, realistic landscape."
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

const result = await fal.subscribe("fal-ai/qwen-image", {
  input: {
    prompt: "Mount Fuji with cherry blossoms in the foreground, clear sky, peaceful spring day, soft natural light, realistic landscape."
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

- [Model Playground](https://fal.ai/models/fal-ai/qwen-image)
- [API Documentation](https://fal.ai/models/fal-ai/qwen-image/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/qwen-image)

### fal.ai Platform

- [Platform Documentation](https://docs.fal.ai)
- [Python Client](https://docs.fal.ai/clients/python)
- [JavaScript Client](https://docs.fal.ai/clients/javascript)
