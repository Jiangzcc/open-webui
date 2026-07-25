# Flux Kontext Lora

> Fast endpoint for the FLUX.1 Kontext [dev] model with LoRA support, enabling rapid and high-quality image editing using pre-trained LoRA adaptations for specific styles, brand identities, and product-specific outputs.


## Overview

- **Endpoint**: `https://fal.run/fal-ai/flux-kontext-lora`
- **Model ID**: `fal-ai/flux-kontext-lora`
- **Category**: image-to-image
- **Kind**: inference
**Tags**: image-editing, image-to-image



## Pricing

- **Price**: $0.035 per megapixels

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`image_url`** (`string`, _required_):
  The URL of the image to edit.
  
  Max width: 14142px, Max height: 14142px, Timeout: 20s
  - Examples: "https://storage.googleapis.com/falserverless/example_inputs/kontext_example_input.webp"

- **`prompt`** (`string`, _required_):
  The prompt to edit the image.
  - Examples: "change the setting to a day time, add a lot of people walking the sidewalk while maintaining the same style of the painting"

- **`num_inference_steps`** (`integer`, _optional_):
  The number of inference steps to perform. Default value: `30`
  - Default: `30`
  - Range: `10` to `50`

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

- **`loras`** (`list<LoraWeight>`, _optional_):
  The LoRAs to use for the image generation. You can use any number of LoRAs
  and they will be merged together to generate the final image.
  - Default: `[]`
  - Array of LoraWeight

- **`acceleration`** (`AccelerationEnum`, _optional_):
  The speed of the generation. The higher the speed, the faster the generation. Default value: `"none"`
  - Default: `"none"`
  - Options: `"none"`, `"regular"`, `"high"`

- **`resolution_mode`** (`ResolutionModeEnum`, _optional_):
  Determines how the output resolution is set for image editing.
  - `auto`: The model selects an optimal resolution from a predefined set that best matches the input image's aspect ratio. This is the recommended setting for most use cases as it's what the model was trained on.
  - `match_input`: The model will attempt to use the same resolution as the input image. The resolution will be adjusted to be compatible with the model's requirements (e.g. dimensions must be multiples of 16 and within supported limits).
  Apart from these, a few aspect ratios are also supported. Default value: `"match_input"`
  - Default: `"match_input"`
  - Options: `"auto"`, `"match_input"`, `"1:1"`, `"16:9"`, `"21:9"`, `"3:2"`, `"2:3"`, `"4:5"`, `"5:4"`, `"3:4"`, `"4:3"`, `"9:16"`, `"9:21"`



**Required Parameters Example**:

```json
{
  "image_url": "https://storage.googleapis.com/falserverless/example_inputs/kontext_example_input.webp",
  "prompt": "change the setting to a day time, add a lot of people walking the sidewalk while maintaining the same style of the painting"
}
```

**Full Example**:

```json
{
  "image_url": "https://storage.googleapis.com/falserverless/example_inputs/kontext_example_input.webp",
  "prompt": "change the setting to a day time, add a lot of people walking the sidewalk while maintaining the same style of the painting",
  "num_inference_steps": 30,
  "guidance_scale": 2.5,
  "num_images": 1,
  "enable_safety_checker": true,
  "output_format": "png",
  "acceleration": "none",
  "resolution_mode": "match_input"
}
```


### Output Schema

The API returns the following output format:

- **`images`** (`list<Image>`, _required_):
  The generated image files info.
  - Array of Image
  - Examples: [{"content_type":"image/jpeg","width":1024,"height":768,"url":"https://storage.googleapis.com/falserverless/example_outputs/kontext_example_output.jpeg"}]

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
      "content_type": "image/jpeg",
      "width": 1024,
      "height": 768,
      "url": "https://storage.googleapis.com/falserverless/example_outputs/kontext_example_output.jpeg"
    }
  ],
  "prompt": ""
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/flux-kontext-lora \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "image_url": "https://storage.googleapis.com/falserverless/example_inputs/kontext_example_input.webp",
     "prompt": "change the setting to a day time, add a lot of people walking the sidewalk while maintaining the same style of the painting"
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
    "fal-ai/flux-kontext-lora",
    arguments={
        "image_url": "https://storage.googleapis.com/falserverless/example_inputs/kontext_example_input.webp",
        "prompt": "change the setting to a day time, add a lot of people walking the sidewalk while maintaining the same style of the painting"
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

const result = await fal.subscribe("fal-ai/flux-kontext-lora", {
  input: {
    image_url: "https://storage.googleapis.com/falserverless/example_inputs/kontext_example_input.webp",
    prompt: "change the setting to a day time, add a lot of people walking the sidewalk while maintaining the same style of the painting"
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

- [Model Playground](https://fal.ai/models/fal-ai/flux-kontext-lora)
- [API Documentation](https://fal.ai/models/fal-ai/flux-kontext-lora/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/flux-kontext-lora)

### fal.ai Platform

- [Platform Documentation](https://docs.fal.ai)
- [Python Client](https://docs.fal.ai/clients/python)
- [JavaScript Client](https://docs.fal.ai/clients/javascript)
