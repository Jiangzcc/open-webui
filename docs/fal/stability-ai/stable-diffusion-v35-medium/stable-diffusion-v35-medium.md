# Stable Diffusion 3.5 Medium

> Stable Diffusion 3.5 Medium is a Multimodal Diffusion Transformer (MMDiT) text-to-image model that features improved performance in image quality, typography, complex prompt understanding, and resource-efficiency.


## Overview

- **Endpoint**: `https://fal.run/fal-ai/stable-diffusion-v35-medium`
- **Model ID**: `fal-ai/stable-diffusion-v35-medium`
- **Category**: text-to-image
- **Kind**: inference
**Tags**: diffusion, typography, style



## Pricing

- **Price**: $0.02 per megapixels

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _required_):
  The prompt to generate an image from.
  - Examples: "A dreamlike Japanese garden in perpetual twilight, bathed in bioluminescent cherry blossoms that emit a soft pink-purple glow. Floating paper lanterns drift lazily through the scene, their warm light creating dancing reflections in a mirror-like koi pond. Ethereal mist weaves between ancient stone pathways lined with glowing mushrooms in pastel blues and purples. A traditional wooden bridge arches gracefully over the water, dusted with fallen petals that sparkle like stardust. The scene is captured through a cinematic lens with perfect bokeh, creating an otherworldly atmosphere. In the background, a crescent moon hangs impossibly large in the sky, surrounded by a sea of stars and auroral wisps in teal and violet. Crystal formations emerge from the ground, refracting the ambient light into rainbow prisms. The entire composition follows the golden ratio, with moody film-like color grading reminiscent of Studio Ghibli, enhanced by volumetric god rays filtering through the luminous foliage. 8K resolution, masterful photography, hyperdetailed, magical realism."

- **`negative_prompt`** (`string`, _optional_):
  The negative prompt to use. Use it to address details that you don't want
  in the image. This could be colors, objects, scenery and even the small details
  (e.g. moustache, blurry, low resolution). Default value: `""`
  - Default: `""`
  - Examples: ""

- **`image_size`** (`ImageSize | Enum`, _optional_):
  The size of the generated image. Default value: `landscape_4_3`
  - Default: `"landscape_4_3"`
  - One of: ImageSize | Enum

- **`num_inference_steps`** (`integer`, _optional_):
  The number of inference steps to perform. Default value: `40`
  - Default: `40`
  - Range: `1` to `50`

- **`seed`** (`integer`, _optional_):
  The same seed and the same prompt given to the same version of the model
  will output the same image every time.

- **`guidance_scale`** (`float`, _optional_):
  The CFG (Classifier Free Guidance) scale is a measure of how close you want
  the model to stick to your prompt when looking for a related image to show you. Default value: `4.5`
  - Default: `4.5`
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
  The format of the generated image. Default value: `"jpeg"`
  - Default: `"jpeg"`
  - Options: `"jpeg"`, `"png"`

- **`auto_fix`** (`boolean`, _optional_):
  If true (default), the requested `image_size` is silently rounded to the nearest compatible value for this model. If false, the request returns a 422 error when the requested `image_size` is not directly compatible. Default value: `true`
  - Default: `true`



**Required Parameters Example**:

```json
{
  "prompt": "A dreamlike Japanese garden in perpetual twilight, bathed in bioluminescent cherry blossoms that emit a soft pink-purple glow. Floating paper lanterns drift lazily through the scene, their warm light creating dancing reflections in a mirror-like koi pond. Ethereal mist weaves between ancient stone pathways lined with glowing mushrooms in pastel blues and purples. A traditional wooden bridge arches gracefully over the water, dusted with fallen petals that sparkle like stardust. The scene is captured through a cinematic lens with perfect bokeh, creating an otherworldly atmosphere. In the background, a crescent moon hangs impossibly large in the sky, surrounded by a sea of stars and auroral wisps in teal and violet. Crystal formations emerge from the ground, refracting the ambient light into rainbow prisms. The entire composition follows the golden ratio, with moody film-like color grading reminiscent of Studio Ghibli, enhanced by volumetric god rays filtering through the luminous foliage. 8K resolution, masterful photography, hyperdetailed, magical realism."
}
```

**Full Example**:

```json
{
  "prompt": "A dreamlike Japanese garden in perpetual twilight, bathed in bioluminescent cherry blossoms that emit a soft pink-purple glow. Floating paper lanterns drift lazily through the scene, their warm light creating dancing reflections in a mirror-like koi pond. Ethereal mist weaves between ancient stone pathways lined with glowing mushrooms in pastel blues and purples. A traditional wooden bridge arches gracefully over the water, dusted with fallen petals that sparkle like stardust. The scene is captured through a cinematic lens with perfect bokeh, creating an otherworldly atmosphere. In the background, a crescent moon hangs impossibly large in the sky, surrounded by a sea of stars and auroral wisps in teal and violet. Crystal formations emerge from the ground, refracting the ambient light into rainbow prisms. The entire composition follows the golden ratio, with moody film-like color grading reminiscent of Studio Ghibli, enhanced by volumetric god rays filtering through the luminous foliage. 8K resolution, masterful photography, hyperdetailed, magical realism.",
  "negative_prompt": "",
  "image_size": "landscape_4_3",
  "num_inference_steps": 40,
  "guidance_scale": 4.5,
  "num_images": 1,
  "enable_safety_checker": true,
  "output_format": "jpeg",
  "auto_fix": true
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
  --url https://fal.run/fal-ai/stable-diffusion-v35-medium \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "A dreamlike Japanese garden in perpetual twilight, bathed in bioluminescent cherry blossoms that emit a soft pink-purple glow. Floating paper lanterns drift lazily through the scene, their warm light creating dancing reflections in a mirror-like koi pond. Ethereal mist weaves between ancient stone pathways lined with glowing mushrooms in pastel blues and purples. A traditional wooden bridge arches gracefully over the water, dusted with fallen petals that sparkle like stardust. The scene is captured through a cinematic lens with perfect bokeh, creating an otherworldly atmosphere. In the background, a crescent moon hangs impossibly large in the sky, surrounded by a sea of stars and auroral wisps in teal and violet. Crystal formations emerge from the ground, refracting the ambient light into rainbow prisms. The entire composition follows the golden ratio, with moody film-like color grading reminiscent of Studio Ghibli, enhanced by volumetric god rays filtering through the luminous foliage. 8K resolution, masterful photography, hyperdetailed, magical realism."
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
    "fal-ai/stable-diffusion-v35-medium",
    arguments={
        "prompt": "A dreamlike Japanese garden in perpetual twilight, bathed in bioluminescent cherry blossoms that emit a soft pink-purple glow. Floating paper lanterns drift lazily through the scene, their warm light creating dancing reflections in a mirror-like koi pond. Ethereal mist weaves between ancient stone pathways lined with glowing mushrooms in pastel blues and purples. A traditional wooden bridge arches gracefully over the water, dusted with fallen petals that sparkle like stardust. The scene is captured through a cinematic lens with perfect bokeh, creating an otherworldly atmosphere. In the background, a crescent moon hangs impossibly large in the sky, surrounded by a sea of stars and auroral wisps in teal and violet. Crystal formations emerge from the ground, refracting the ambient light into rainbow prisms. The entire composition follows the golden ratio, with moody film-like color grading reminiscent of Studio Ghibli, enhanced by volumetric god rays filtering through the luminous foliage. 8K resolution, masterful photography, hyperdetailed, magical realism."
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

const result = await fal.subscribe("fal-ai/stable-diffusion-v35-medium", {
  input: {
    prompt: "A dreamlike Japanese garden in perpetual twilight, bathed in bioluminescent cherry blossoms that emit a soft pink-purple glow. Floating paper lanterns drift lazily through the scene, their warm light creating dancing reflections in a mirror-like koi pond. Ethereal mist weaves between ancient stone pathways lined with glowing mushrooms in pastel blues and purples. A traditional wooden bridge arches gracefully over the water, dusted with fallen petals that sparkle like stardust. The scene is captured through a cinematic lens with perfect bokeh, creating an otherworldly atmosphere. In the background, a crescent moon hangs impossibly large in the sky, surrounded by a sea of stars and auroral wisps in teal and violet. Crystal formations emerge from the ground, refracting the ambient light into rainbow prisms. The entire composition follows the golden ratio, with moody film-like color grading reminiscent of Studio Ghibli, enhanced by volumetric god rays filtering through the luminous foliage. 8K resolution, masterful photography, hyperdetailed, magical realism."
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

- [Model Playground](https://fal.ai/models/fal-ai/stable-diffusion-v35-medium)
- [API Documentation](https://fal.ai/models/fal-ai/stable-diffusion-v35-medium/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/stable-diffusion-v35-medium)
- [GitHub Repository](https://stability.ai/license)

### fal.ai Platform

- [Platform Documentation](https://docs.fal.ai)
- [Python Client](https://docs.fal.ai/clients/python)
- [JavaScript Client](https://docs.fal.ai/clients/javascript)
