# PixArt-Σ

> Weak-to-Strong Training of Diffusion Transformer for 4K Text-to-Image Generation


## Overview

- **Endpoint**: `https://fal.run/fal-ai/pixart-sigma`
- **Model ID**: `fal-ai/pixart-sigma`
- **Category**: text-to-image
- **Kind**: inference
**Tags**: diffusion



## Pricing

- **Price**: $0 per compute seconds

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _required_):
  The prompt to use for generating the image. Be as descriptive as possible for best results.
  - Examples: "Photorealistic closeup video of two pirate ships battling each other as they sail inside a cup of coffee.", "an astronaut sitting in a diner, eating fries, cinematic, analog film", "Pirate ship trapped in a cosmic maelstrom nebula, rendered in cosmic beach whirlpool engine, volumetric lighting, spectacular, ambient lights, light pollution, cinematic atmosphere, art nouveau style, illustration art artwork by SenseiJaye, intricate detail.", "stars, water, brilliantly, gorgeous large scale scene, a little girl, in the style of dreamy realism, light gold and amber, blue and pink, brilliantly illuminated in the background.", "professional portrait photo of an anthropomorphic cat wearing fancy gentleman hat and jacket walking in autumn forest.", "beautiful lady, freckles, big smile, blue eyes, short ginger hair, dark makeup, wearing a floral blue vest top, soft light, dark grey background", "Spectacular Tiny World in the Transparent Jar On the Table, interior of the Great Hall, Elaborate, Carved Architecture, Anatomy, Symmetrical, Geometric and Parameteric Details, Precision Flat line Details, Pattern, Dark fantasy, Dark errie mood and ineffably mysterious mood, Technical design, Intricate Ultra Detail, Ornate Detail, Stylized and Futuristic and Biomorphic Details, Architectural Concept, Low contrast Details, Cinematic Lighting, 8k, by moebius, Fullshot, Epic, Fullshot, Octane render, Unreal ,Photorealistic, Hyperrealism", "anthropomorphic profile of the white snow owl Crystal priestess , art deco painting, pretty and expressive eyes, ornate costume, mythical, ethereal, intricate, elaborate, hyperrealism, hyper detailed, 3D, 8K, Ultra Realistic, high octane, ultra resolution, amazing detail, perfection, In frame, photorealistic, cinematic lighting, visual clarity, shading , Lumen Reflections, Super-Resolution, gigapixel, color grading, retouch, enhanced, PBR, Blender, V-ray, Procreate, zBrush, Unreal Engine 5, cinematic, volumetric, dramatic, neon lighting, wide angle lens ,no digital painting blur", "The parametric hotel lobby is a sleek and modern space with plenty of natural light. The lobby is spacious and open with a variety of seating options. The front desk is a sleek white counter with a parametric design. The walls are a light blue color with parametric patterns. The floor is a light wood color with a parametric design. There are plenty of plants and flowers throughout the space. The overall effect is a calm and relaxing space. occlusion, moody, sunset, concept art, octane rendering, 8k, highly detailed, concept art, highly detailed, beautiful scenery, cinematic, beautiful light, hyperreal, octane render, hdr, long exposure, 8K, realistic, fog, moody, fire and explosions, smoke, 50mm f2.8"

- **`negative_prompt`** (`string`, _optional_):
  The negative prompt to use. Use it to address details that you don't want
  in the image. This could be colors, objects, scenery and even the small details
  (e.g. moustache, blurry, low resolution). Default value: `""`
  - Default: `""`
  - Examples: "cartoon, illustration, animation. face. male, female", "ugly, deformed"

- **`style`** (`StyleEnum`, _optional_):
  The style to apply to the image. Default value: `"(No style)"`
  - Default: `"(No style)"`
  - Options: `"(No style)"`, `"Cinematic"`, `"Photographic"`, `"Anime"`, `"Manga"`, `"Digital Art"`, `"Pixel art"`, `"Fantasy art"`, `"Neonpunk"`, `"3D Model"`

- **`image_size`** (`ImageSize | Enum`, _optional_):
  The size of the generated image. Default value: `square_hd`
  - Default: `"square_hd"`
  - One of: ImageSize | Enum

- **`num_inference_steps`** (`integer`, _optional_):
  The number of inference steps to perform. Default value: `35`
  - Default: `35`
  - Range: `5` to `50`

- **`scheduler`** (`SchedulerEnum`, _optional_):
  The scheduler to use for the model. Default value: `"DPM-SOLVER"`
  - Default: `"DPM-SOLVER"`
  - Options: `"DPM-SOLVER"`, `"SA-SOLVER"`

- **`guidance_scale`** (`float`, _optional_):
  The CFG (Classifier Free Guidance) scale is a measure of how close you want
  the model to stick to your prompt when looking for a related image to show you. Default value: `4.5`
  - Default: `4.5`
  - Range: `1` to `10`

- **`seed`** (`integer`, _optional_):
  The same seed and the same prompt given to the same version of Stable Diffusion
  will output the same image every time.

- **`sync_mode`** (`boolean`, _optional_):
  If `True`, the media will be returned as a data URI and the output data won't be available in the request history.
  - Default: `false`

- **`num_images`** (`integer`, _optional_):
  The number of images to generate. Default value: `1`
  - Default: `1`
  - Range: `1` to `8`

- **`enable_safety_checker`** (`boolean`, _optional_):
  If set to true, the safety checker will be enabled.
  - Default: `false`



**Required Parameters Example**:

```json
{
  "prompt": "Photorealistic closeup video of two pirate ships battling each other as they sail inside a cup of coffee."
}
```

**Full Example**:

```json
{
  "prompt": "Photorealistic closeup video of two pirate ships battling each other as they sail inside a cup of coffee.",
  "negative_prompt": "cartoon, illustration, animation. face. male, female",
  "style": "(No style)",
  "image_size": "square_hd",
  "num_inference_steps": 35,
  "scheduler": "DPM-SOLVER",
  "guidance_scale": 4.5,
  "num_images": 1
}
```


### Output Schema

The API returns the following output format:

- **`images`** (`list<Image>`, _required_):
  The generated image files info.
  - Array of Image

- **`timings`** (`Timings`, _required_):
  The timings of the different steps of the generation process.

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
      "content_type": "image/png",
      "file_name": "z9RV14K95DvU.png",
      "file_size": 4404019,
      "width": 1024,
      "height": 1024
    }
  ],
  "prompt": ""
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/pixart-sigma \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "Photorealistic closeup video of two pirate ships battling each other as they sail inside a cup of coffee."
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
    "fal-ai/pixart-sigma",
    arguments={
        "prompt": "Photorealistic closeup video of two pirate ships battling each other as they sail inside a cup of coffee."
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

const result = await fal.subscribe("fal-ai/pixart-sigma", {
  input: {
    prompt: "Photorealistic closeup video of two pirate ships battling each other as they sail inside a cup of coffee."
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

- [Model Playground](https://fal.ai/models/fal-ai/pixart-sigma)
- [API Documentation](https://fal.ai/models/fal-ai/pixart-sigma/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/pixart-sigma)
- [GitHub Repository](https://github.com/PixArt-alpha/PixArt-sigma/blob/master/LICENSE)

### fal.ai Platform

- [Platform Documentation](https://docs.fal.ai)
- [Python Client](https://docs.fal.ai/clients/python)
- [JavaScript Client](https://docs.fal.ai/clients/javascript)
