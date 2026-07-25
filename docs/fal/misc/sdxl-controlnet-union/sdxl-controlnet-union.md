# SDXL ControlNet Union

> An efficent SDXL multi-controlnet text-to-image model.


## Overview

- **Endpoint**: `https://fal.run/fal-ai/sdxl-controlnet-union`
- **Model ID**: `fal-ai/sdxl-controlnet-union`
- **Category**: text-to-image
- **Kind**: inference
**Tags**: diffusion, controlnet, composition



## Pricing

- **Price**: $0 per compute seconds

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`enable_safety_checker`** (`boolean`, _optional_):
  If set to true, the safety checker will be enabled. Default value: `true`
  - Default: `true`

- **`sync_mode`** (`boolean`, _optional_):
  If `True`, the media will be returned as a data URI and the output data won't be available in the request history.
  - Default: `false`

- **`guidance_scale`** (`float`, _optional_):
  The CFG (Classifier Free Guidance) scale is a measure of how close you want
  the model to stick to your prompt when looking for a related image to show you. Default value: `7.5`
  - Default: `7.5`
  - Range: `0` to `20`

- **`num_inference_steps`** (`integer`, _optional_):
  The number of inference steps to perform. Default value: `35`
  - Default: `35`
  - Range: `1` to `70`

- **`teed_image_url`** (`string`, _optional_):
  The URL of the control image. Default value: `"null"`
  - Default: `null`
  - Examples: "https://fal-cdn.batuhan-941.workers.dev/files/rabbit/MiN_j3St9B8esJleCZKMU.jpeg"

- **`depth_image_url`** (`string`, _optional_):
  The URL of the control image. Default value: `"null"`
  - Default: `null`
  - Examples: "https://fal-cdn.batuhan-941.workers.dev/files/rabbit/MiN_j3St9B8esJleCZKMU.jpeg"

- **`canny_preprocess`** (`boolean`, _optional_):
  Whether to preprocess the canny image. Default value: `true`
  - Default: `true`

- **`segmentation_image_url`** (`string`, _optional_):
  The URL of the control image. Default value: `"null"`
  - Default: `null`
  - Examples: "https://fal-cdn.batuhan-941.workers.dev/files/rabbit/MiN_j3St9B8esJleCZKMU.jpeg"

- **`num_images`** (`integer`, _optional_):
  The number of images to generate. Default value: `1`
  - Default: `1`
  - Range: `1` to `8`

- **`segmentation_preprocess`** (`boolean`, _optional_):
  Whether to preprocess the segmentation image. Default value: `true`
  - Default: `true`

- **`expand_prompt`** (`boolean`, _optional_):
  If set to true, the prompt will be expanded with additional prompts.
  - Default: `false`

- **`request_id`** (`string`, _optional_):
  An id bound to a request, can be used with response to identify the request
  itself. Default value: `""`
  - Default: `""`

- **`loras`** (`list<LoraWeight>`, _optional_):
  The list of LoRA weights to use.
  - Default: `[]`
  - Array of LoraWeight

- **`controlnet_conditioning_scale`** (`float`, _optional_):
  The scale of the controlnet conditioning. Default value: `0.5`
  - Default: `0.5`
  - Range: `0` to `1`

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

- **`prompt`** (`string`, _required_):
  The prompt to use for generating the image. Be as descriptive as possible for best results.
  - Examples: "Ice fortress, aurora skies, polar wildlife, twilight"

- **`normal_image_url`** (`string`, _optional_):
  The URL of the control image. Default value: `"null"`
  - Default: `null`
  - Examples: "https://fal-cdn.batuhan-941.workers.dev/files/rabbit/MiN_j3St9B8esJleCZKMU.jpeg"

- **`depth_preprocess`** (`boolean`, _optional_):
  Whether to preprocess the depth image. Default value: `true`
  - Default: `true`

- **`canny_image_url`** (`string`, _optional_):
  The URL of the control image. Default value: `"null"`
  - Default: `null`
  - Examples: "https://fal-cdn.batuhan-941.workers.dev/files/rabbit/MiN_j3St9B8esJleCZKMU.jpeg"

- **`openpose_preprocess`** (`boolean`, _optional_):
  Whether to preprocess the openpose image. Default value: `true`
  - Default: `true`

- **`normal_preprocess`** (`boolean`, _optional_):
  Whether to preprocess the normal image. Default value: `true`
  - Default: `true`

- **`image_size`** (`ImageSize | Enum`, _optional_):
  The size of the generated image. Leave it none to automatically infer from the control image.
  - Default: `null`
  - One of: ImageSize | Enum
  - Examples: null

- **`format`** (`FormatEnum`, _optional_):
  The format of the generated image. Default value: `"jpeg"`
  - Default: `"jpeg"`
  - Options: `"jpeg"`, `"png"`

- **`openpose_image_url`** (`string`, _optional_):
  The URL of the control image. Default value: `"null"`
  - Default: `null`
  - Examples: "https://fal-cdn.batuhan-941.workers.dev/files/rabbit/MiN_j3St9B8esJleCZKMU.jpeg"

- **`seed`** (`integer`, _optional_):
  The same seed and the same prompt given to the same version of Stable Diffusion
  will output the same image every time.
  - Default: `null`

- **`teed_preprocess`** (`boolean`, _optional_):
  Whether to preprocess the teed image. Default value: `true`
  - Default: `true`

- **`safety_checker_version`** (`SafetyCheckerVersionEnum`, _optional_):
  The version of the safety checker to use. v1 is the default CompVis safety checker. v2 uses a custom ViT model. Default value: `"v1"`
  - Default: `"v1"`
  - Options: `"v1"`, `"v2"`



**Required Parameters Example**:

```json
{
  "prompt": "Ice fortress, aurora skies, polar wildlife, twilight"
}
```

**Full Example**:

```json
{
  "enable_safety_checker": true,
  "guidance_scale": 7.5,
  "num_inference_steps": 35,
  "teed_image_url": "https://fal-cdn.batuhan-941.workers.dev/files/rabbit/MiN_j3St9B8esJleCZKMU.jpeg",
  "depth_image_url": "https://fal-cdn.batuhan-941.workers.dev/files/rabbit/MiN_j3St9B8esJleCZKMU.jpeg",
  "canny_preprocess": true,
  "segmentation_image_url": "https://fal-cdn.batuhan-941.workers.dev/files/rabbit/MiN_j3St9B8esJleCZKMU.jpeg",
  "num_images": 1,
  "segmentation_preprocess": true,
  "loras": [],
  "controlnet_conditioning_scale": 0.5,
  "negative_prompt": "cartoon, illustration, animation. face. male, female",
  "embeddings": [],
  "prompt": "Ice fortress, aurora skies, polar wildlife, twilight",
  "normal_image_url": "https://fal-cdn.batuhan-941.workers.dev/files/rabbit/MiN_j3St9B8esJleCZKMU.jpeg",
  "depth_preprocess": true,
  "canny_image_url": "https://fal-cdn.batuhan-941.workers.dev/files/rabbit/MiN_j3St9B8esJleCZKMU.jpeg",
  "openpose_preprocess": true,
  "normal_preprocess": true,
  "image_size": null,
  "format": "jpeg",
  "openpose_image_url": "https://fal-cdn.batuhan-941.workers.dev/files/rabbit/MiN_j3St9B8esJleCZKMU.jpeg",
  "teed_preprocess": true,
  "safety_checker_version": "v1"
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
  --url https://fal.run/fal-ai/sdxl-controlnet-union \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "Ice fortress, aurora skies, polar wildlife, twilight"
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
    "fal-ai/sdxl-controlnet-union",
    arguments={
        "prompt": "Ice fortress, aurora skies, polar wildlife, twilight"
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

const result = await fal.subscribe("fal-ai/sdxl-controlnet-union", {
  input: {
    prompt: "Ice fortress, aurora skies, polar wildlife, twilight"
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

- [Model Playground](https://fal.ai/models/fal-ai/sdxl-controlnet-union)
- [API Documentation](https://fal.ai/models/fal-ai/sdxl-controlnet-union/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/sdxl-controlnet-union)
- [GitHub Repository](https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/blob/main/LICENSE.md)

### fal.ai Platform

- [Platform Documentation](https://docs.fal.ai)
- [Python Client](https://docs.fal.ai/clients/python)
- [JavaScript Client](https://docs.fal.ai/clients/javascript)
