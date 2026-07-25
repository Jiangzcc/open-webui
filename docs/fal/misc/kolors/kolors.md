# Kolors

> Photorealistic Text-to-Image


## Overview

- **Endpoint**: `https://fal.run/fal-ai/kolors`
- **Model ID**: `fal-ai/kolors`
- **Category**: text-to-image
- **Kind**: inference
**Tags**: realism, diffusion



## Pricing

- **Price**: $0 per compute seconds

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _required_):
  The prompt to use for generating the image. Be as descriptive as possible
  for best results.
  - Examples: "A young Chinese couple with fair skin, dressed in stylish sportswear, with the modern Beijing city skyline in the background. Facial details, clear pores, captured using the latest camera model, close-up shot, ultra-high quality, 8K, visual feast.", "The image features four mythical beasts: Vermilion Bird, Black Tortoise, Azure Dragon, and White Tiger. The Vermilion Bird is at the top of the image, with feathers as red as fire and a tail as magnificent as a phoenix, its wings spreading like burning flames. The Black Tortoise is at the bottom, depicted as a giant turtle intertwined with a snake. Ancient runes adorn the turtle's shell, and the snake's eyes are cold and sharp. The Azure Dragon is on the right, its long body coiling in the sky, with jade-green scales, flowing whiskers, deer-like horns, and exhaling clouds and mist. The White Tiger is on the left, with a majestic posture, white fur with black stripes, piercing eyes, sharp teeth and claws, surrounded by vast mountains and grasslands."

- **`negative_prompt`** (`string`, _optional_):
  The negative prompt to use. Use it to address details that you don't want
  in the image. This could be colors, objects, scenery and even the small
  details (e.g. moustache, blurry, low resolution). Default value: `""`
  - Default: `""`
  - Examples: "ugly, deformed, blurry"

- **`guidance_scale`** (`float`, _optional_):
  The CFG (Classifier Free Guidance) scale is a measure of how close you want
  the model to stick to your prompt when looking for a related image to show
  you. Default value: `5`
  - Default: `5`
  - Range: `1` to `10`

- **`num_inference_steps`** (`integer`, _optional_):
  The number of inference steps to perform. Default value: `50`
  - Default: `50`
  - Range: `1` to `150`

- **`seed`** (`integer`, _optional_):
  Seed

- **`sync_mode`** (`boolean`, _optional_):
  If `True`, the media will be returned as a data URI and the output data won't be available in the request history.
  - Default: `false`

- **`enable_safety_checker`** (`boolean`, _optional_):
  Enable safety checker. Default value: `true`
  - Default: `true`

- **`num_images`** (`integer`, _optional_):
  The number of images to generate. Default value: `1`
  - Default: `1`
  - Range: `1` to `8`

- **`image_size`** (`ImageSize | Enum`, _optional_):
  The size of the generated image. Default value: `square_hd`
  - Default: `"square_hd"`
  - One of: ImageSize | Enum

- **`scheduler`** (`SchedulerEnum`, _optional_):
  The scheduler to use for the model. Default value: `"EulerDiscreteScheduler"`
  - Default: `"EulerDiscreteScheduler"`
  - Options: `"EulerDiscreteScheduler"`, `"EulerAncestralDiscreteScheduler"`, `"DPMSolverMultistepScheduler"`, `"DPMSolverMultistepScheduler_SDE_karras"`, `"UniPCMultistepScheduler"`, `"DEISMultistepScheduler"`

- **`output_format`** (`OutputFormatEnum`, _optional_):
  The format of the generated image. Default value: `"png"`
  - Default: `"png"`
  - Options: `"jpeg"`, `"png"`



**Required Parameters Example**:

```json
{
  "prompt": "A young Chinese couple with fair skin, dressed in stylish sportswear, with the modern Beijing city skyline in the background. Facial details, clear pores, captured using the latest camera model, close-up shot, ultra-high quality, 8K, visual feast."
}
```

**Full Example**:

```json
{
  "prompt": "A young Chinese couple with fair skin, dressed in stylish sportswear, with the modern Beijing city skyline in the background. Facial details, clear pores, captured using the latest camera model, close-up shot, ultra-high quality, 8K, visual feast.",
  "negative_prompt": "ugly, deformed, blurry",
  "guidance_scale": 5,
  "num_inference_steps": 50,
  "enable_safety_checker": true,
  "num_images": 1,
  "image_size": "square_hd",
  "scheduler": "EulerDiscreteScheduler",
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
  --url https://fal.run/fal-ai/kolors \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "A young Chinese couple with fair skin, dressed in stylish sportswear, with the modern Beijing city skyline in the background. Facial details, clear pores, captured using the latest camera model, close-up shot, ultra-high quality, 8K, visual feast."
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
    "fal-ai/kolors",
    arguments={
        "prompt": "A young Chinese couple with fair skin, dressed in stylish sportswear, with the modern Beijing city skyline in the background. Facial details, clear pores, captured using the latest camera model, close-up shot, ultra-high quality, 8K, visual feast."
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

const result = await fal.subscribe("fal-ai/kolors", {
  input: {
    prompt: "A young Chinese couple with fair skin, dressed in stylish sportswear, with the modern Beijing city skyline in the background. Facial details, clear pores, captured using the latest camera model, close-up shot, ultra-high quality, 8K, visual feast."
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

- [Model Playground](https://fal.ai/models/fal-ai/kolors)
- [API Documentation](https://fal.ai/models/fal-ai/kolors/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/kolors)
- [GitHub Repository](https://huggingface.co/Kwai-Kolors/Kolors-diffusers/raw/main/MODEL_LICENSE)

### fal.ai Platform

- [Platform Documentation](https://docs.fal.ai)
- [Python Client](https://docs.fal.ai/clients/python)
- [JavaScript Client](https://docs.fal.ai/clients/javascript)
