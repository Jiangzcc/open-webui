# Playground v2.5

> State-of-the-art open-source model in aesthetic quality


## Overview

- **Endpoint**: `https://fal.run/fal-ai/playground-v25`
- **Model ID**: `fal-ai/playground-v25`
- **Category**: text-to-image
- **Kind**: inference
**Tags**: artistic, style



## Pricing

- **Price**: $0 per compute seconds

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`image_size`** (`ImageSize | Enum`, _optional_):
  The size of the generated image. Default value: `square_hd`
  - Default: `"square_hd"`
  - One of: ImageSize | Enum

- **`negative_prompt`** (`string`, _optional_):
  The negative prompt to use. Use it to address details that you don't want
  in the image. This could be colors, objects, scenery and even the small details
  (e.g. moustache, blurry, low resolution). Default value: `""`
  - Default: `""`
  - Examples: "cartoon, illustration, animation. face. male, female", "ugly, deformed"

- **`embeddings`** (`list<Embedding>`, _optional_):
  The list of embeddings to use.
  - Default: `[]`
  - Array of Embedding

- **`guidance_scale`** (`float`, _optional_):
  The CFG (Classifier Free Guidance) scale is a measure of how close you want
  the model to stick to your prompt when looking for a related image to show you. Default value: `3`
  - Default: `3`
  - Range: `0` to `20`

- **`safety_checker_version`** (`SafetyCheckerVersionEnum`, _optional_):
  The version of the safety checker to use. v1 is the default CompVis safety checker. v2 uses a custom ViT model. Default value: `"v1"`
  - Default: `"v1"`
  - Options: `"v1"`, `"v2"`

- **`expand_prompt`** (`boolean`, _optional_):
  If set to true, the prompt will be expanded with additional prompts.
  - Default: `false`

- **`num_images`** (`integer`, _optional_):
  The number of images to generate. Default value: `1`
  - Default: `1`
  - Range: `1` to `8`

- **`format`** (`FormatEnum`, _optional_):
  The format of the generated image. Default value: `"jpeg"`
  - Default: `"jpeg"`
  - Options: `"jpeg"`, `"png"`

- **`num_inference_steps`** (`integer`, _optional_):
  The number of inference steps to perform. Default value: `25`
  - Default: `25`
  - Range: `1` to `50`

- **`enable_safety_checker`** (`boolean`, _optional_):
  If set to true, the safety checker will be enabled. Default value: `true`
  - Default: `true`

- **`prompt`** (`string`, _required_):
  The prompt to use for generating the image. Be as descriptive as possible for best results.
  - Examples: "Masterpiece (wide angle shot) , Easterbunny crafting an incantation, (creating a little colorful magic egg in a nest:1.6), standing on an old carved table in a colorful factory laboratory. fantastic view"

- **`seed`** (`integer`, _optional_):
  The same seed and the same prompt given to the same version of Stable Diffusion
  will output the same image every time.
  - Default: `null`

- **`request_id`** (`string`, _optional_):
  An id bound to a request, can be used with response to identify the request
  itself. Default value: `""`
  - Default: `""`



**Required Parameters Example**:

```json
{
  "prompt": "Masterpiece (wide angle shot) , Easterbunny crafting an incantation, (creating a little colorful magic egg in a nest:1.6), standing on an old carved table in a colorful factory laboratory. fantastic view"
}
```

**Full Example**:

```json
{
  "image_size": "square_hd",
  "negative_prompt": "cartoon, illustration, animation. face. male, female",
  "embeddings": [],
  "guidance_scale": 3,
  "safety_checker_version": "v1",
  "num_images": 1,
  "format": "jpeg",
  "num_inference_steps": 25,
  "enable_safety_checker": true,
  "prompt": "Masterpiece (wide angle shot) , Easterbunny crafting an incantation, (creating a little colorful magic egg in a nest:1.6), standing on an old carved table in a colorful factory laboratory. fantastic view"
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
  --url https://fal.run/fal-ai/playground-v25 \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "Masterpiece (wide angle shot) , Easterbunny crafting an incantation, (creating a little colorful magic egg in a nest:1.6), standing on an old carved table in a colorful factory laboratory. fantastic view"
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
    "fal-ai/playground-v25",
    arguments={
        "prompt": "Masterpiece (wide angle shot) , Easterbunny crafting an incantation, (creating a little colorful magic egg in a nest:1.6), standing on an old carved table in a colorful factory laboratory. fantastic view"
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

const result = await fal.subscribe("fal-ai/playground-v25", {
  input: {
    prompt: "Masterpiece (wide angle shot) , Easterbunny crafting an incantation, (creating a little colorful magic egg in a nest:1.6), standing on an old carved table in a colorful factory laboratory. fantastic view"
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

- [Model Playground](https://fal.ai/models/fal-ai/playground-v25)
- [API Documentation](https://fal.ai/models/fal-ai/playground-v25/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/playground-v25)
- [GitHub Repository](https://huggingface.co/playgroundai/playground-v2.5-1024px-aesthetic/blob/main/LICENSE.md)

### fal.ai Platform

- [Platform Documentation](https://docs.fal.ai)
- [Python Client](https://docs.fal.ai/clients/python)
- [JavaScript Client](https://docs.fal.ai/clients/javascript)
