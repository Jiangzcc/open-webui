# Cosmos 3 Super Image to Video

> Cosmos3 is a collection of Omnimodal world models capable of generating dynamic, high-quality video, image, audio, and action commands from combinations of text, image, video, and action trajectory inputs.


## Overview

- **Endpoint**: `https://fal.run/nvidia/cosmos-3-super/image-to-video`
- **Model ID**: `nvidia/cosmos-3-super/image-to-video`
- **Category**: image-to-video
- **Kind**: inference
**Tags**: stylized, transform, lipsync



## Pricing

Your request will cost **$0.05** per second of generated video, rounded up. Agentic generation is billed for each candidate video generated

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _required_):
  Text prompt describing the motion and scene of the video to generate.
  - Examples: "The camera slowly pushes in as the subject turns their head toward the light, hair drifting in a gentle breeze, dust motes floating through warm afternoon sun."

- **`image_url`** (`string`, _required_):
  URL of the conditioning first-frame image for the video.
  - Examples: "https://storage.googleapis.com/falserverless/example_inputs/hunyuan_i2v.jpg"

- **`negative_prompt`** (`string`, _optional_):
  Content to steer the generation away from (artifacts, unwanted motion). Defaults to NVIDIA's recommended i2v negative prompt; pass an empty string to disable. Default value: `"The video captures a series of frames showing macroblocking artifacts, chromatic aberration, high-frequency noise, and rolling shutter distortion. It includes static with no motion, motion blur, over-saturation, shaky footage, low resolution, grainy texture, pixelated images, poorly lit areas, underexposed and overexposed scenes, poor color balance, washed out colors, choppy sequences, jerky movements, low frame rate, bit-depth compression artifacts, color banding, unnatural transitions, outdated special effects, fake elements, unconvincing visuals, poorly edited content, jump cuts, hard cut, visual noise, and flickering. It features moiré patterns, edge halos, and temporal aliasing. Furthermore, the content defies common sense, generating illogical scenarios, nonsensical entities, absurd character behaviors, and conceptual paradoxes that violate basic human reasoning and everyday reality. The video looks like a surreal or glitchy hallucination. Overall, the video is of poor quality."`
  - Default: `"The video captures a series of frames showing macroblocking artifacts, chromatic aberration, high-frequency noise, and rolling shutter distortion. It includes static with no motion, motion blur, over-saturation, shaky footage, low resolution, grainy texture, pixelated images, poorly lit areas, underexposed and overexposed scenes, poor color balance, washed out colors, choppy sequences, jerky movements, low frame rate, bit-depth compression artifacts, color banding, unnatural transitions, outdated special effects, fake elements, unconvincing visuals, poorly edited content, jump cuts, hard cut, visual noise, and flickering. It features moiré patterns, edge halos, and temporal aliasing. Furthermore, the content defies common sense, generating illogical scenarios, nonsensical entities, absurd character behaviors, and conceptual paradoxes that violate basic human reasoning and everyday reality. The video looks like a surreal or glitchy hallucination. Overall, the video is of poor quality."`
  - Examples: "The video captures a series of frames showing macroblocking artifacts, chromatic aberration, high-frequency noise, and rolling shutter distortion. It includes static with no motion, motion blur, over-saturation, shaky footage, low resolution, grainy texture, pixelated images, poorly lit areas, underexposed and overexposed scenes, poor color balance, washed out colors, choppy sequences, jerky movements, low frame rate, bit-depth compression artifacts, color banding, unnatural transitions, outdated special effects, fake elements, unconvincing visuals, poorly edited content, jump cuts, hard cut, visual noise, and flickering. It features moiré patterns, edge halos, and temporal aliasing. Furthermore, the content defies common sense, generating illogical scenarios, nonsensical entities, absurd character behaviors, and conceptual paradoxes that violate basic human reasoning and everyday reality. The video looks like a surreal or glitchy hallucination. Overall, the video is of poor quality."

- **`enable_prompt_expansion`** (`boolean`, _optional_):
  If true, the Cosmos3-Nano Reasoner (a VLM that sees the first frame) rewrites the prompt into the dense caption Cosmos3 was trained on. The app starts a local Reasoner by default, or uses COSMOS_PROMPT_UPSAMPLER_BASE_URL when configured. Falls back to the raw prompt if expansion fails. Default value: `true`
  - Default: `true`

- **`enable_agentic_generation`** (`boolean`, _optional_):
  Enable the iterative Cosmos agentic loop: prompt upsampling, candidate video generation, VLM critique of sampled frames, and prompt rewrite. Each candidate is a full render, so this is substantially slower and costlier than a single generation.
  - Default: `false`

- **`agentic_max_iterations`** (`integer`, _optional_):
  Maximum agentic prompt stages when agentic generation is enabled. Default value: `2`
  - Default: `2`
  - Range: `1` to `3`

- **`agentic_samples_per_iteration`** (`integer`, _optional_):
  Candidate videos to generate and judge per agentic iteration. The best candidate advances to the next rewrite stage. Default value: `2`
  - Default: `2`
  - Range: `1` to `3`

- **`agentic_early_stop`** (`boolean`, _optional_):
  Stop the agentic loop early when the critic score clears the strict quality threshold. Default value: `true`
  - Default: `true`

- **`image_size`** (`ImageSize | Enum`, _optional_):
  The size of the generated video. The request is clamped and snapped to the nearest supported NVIDIA tier (256p/480p/720p) and aspect ratio.
  - Default: `{"width":832,"height":480}`
  - One of: ImageSize | Enum
  - Examples: {"width":832,"height":480}

- **`num_frames`** (`integer`, _optional_):
  Number of frames to generate. More frames yield a longer video. Default value: `189`
  - Default: `189`
  - Range: `5` to `189`

- **`frames_per_second`** (`integer`, _optional_):
  Frames per second of the output video. Default value: `24`
  - Default: `24`
  - Range: `4` to `60`

- **`num_inference_steps`** (`integer`, _optional_):
  Number of denoising steps. More steps yield higher quality but take longer. Default value: `28`
  - Default: `28`
  - Range: `1` to `50`

- **`guidance_scale`** (`float`, _optional_):
  Classifier-free guidance scale. Higher values increase prompt adherence at the cost of diversity. Default value: `6`
  - Default: `6`
  - Range: `0` to `20`

- **`seed`** (`integer`, _optional_):
  The same seed and prompt given to the same model version will produce the same video every time.

- **`enable_safety_checker`** (`boolean`, _optional_):
  Enable content moderation for the input prompt and image. Default value: `true`
  - Default: `true`

- **`sync_mode`** (`boolean`, _optional_):
  If `True`, the video is returned as a data URI and the output data won't be available in the request history.
  - Default: `false`



**Required Parameters Example**:

```json
{
  "prompt": "The camera slowly pushes in as the subject turns their head toward the light, hair drifting in a gentle breeze, dust motes floating through warm afternoon sun.",
  "image_url": "https://storage.googleapis.com/falserverless/example_inputs/hunyuan_i2v.jpg"
}
```

**Full Example**:

```json
{
  "prompt": "The camera slowly pushes in as the subject turns their head toward the light, hair drifting in a gentle breeze, dust motes floating through warm afternoon sun.",
  "image_url": "https://storage.googleapis.com/falserverless/example_inputs/hunyuan_i2v.jpg",
  "negative_prompt": "The video captures a series of frames showing macroblocking artifacts, chromatic aberration, high-frequency noise, and rolling shutter distortion. It includes static with no motion, motion blur, over-saturation, shaky footage, low resolution, grainy texture, pixelated images, poorly lit areas, underexposed and overexposed scenes, poor color balance, washed out colors, choppy sequences, jerky movements, low frame rate, bit-depth compression artifacts, color banding, unnatural transitions, outdated special effects, fake elements, unconvincing visuals, poorly edited content, jump cuts, hard cut, visual noise, and flickering. It features moiré patterns, edge halos, and temporal aliasing. Furthermore, the content defies common sense, generating illogical scenarios, nonsensical entities, absurd character behaviors, and conceptual paradoxes that violate basic human reasoning and everyday reality. The video looks like a surreal or glitchy hallucination. Overall, the video is of poor quality.",
  "enable_prompt_expansion": true,
  "agentic_max_iterations": 2,
  "agentic_samples_per_iteration": 2,
  "agentic_early_stop": true,
  "image_size": {
    "width": 832,
    "height": 480
  },
  "num_frames": 189,
  "frames_per_second": 24,
  "num_inference_steps": 28,
  "guidance_scale": 6,
  "enable_safety_checker": true
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`VideoFile`, _required_):
  The generated video.
  - Examples: {"content_type":"video/mp4","url":"https://v3b.fal.media/files/b/0a8fc99c/cosmos3-i2v-example.mp4"}

- **`seed`** (`integer`, _required_):
  The seed used for generation.
  - Examples: 1143



**Example Response**:

```json
{
  "video": {
    "content_type": "video/mp4",
    "url": "https://v3b.fal.media/files/b/0a8fc99c/cosmos3-i2v-example.mp4"
  },
  "seed": 1143
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/nvidia/cosmos-3-super/image-to-video \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "The camera slowly pushes in as the subject turns their head toward the light, hair drifting in a gentle breeze, dust motes floating through warm afternoon sun.",
     "image_url": "https://storage.googleapis.com/falserverless/example_inputs/hunyuan_i2v.jpg"
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
    "nvidia/cosmos-3-super/image-to-video",
    arguments={
        "prompt": "The camera slowly pushes in as the subject turns their head toward the light, hair drifting in a gentle breeze, dust motes floating through warm afternoon sun.",
        "image_url": "https://storage.googleapis.com/falserverless/example_inputs/hunyuan_i2v.jpg"
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

const result = await fal.subscribe("nvidia/cosmos-3-super/image-to-video", {
  input: {
    prompt: "The camera slowly pushes in as the subject turns their head toward the light, hair drifting in a gentle breeze, dust motes floating through warm afternoon sun.",
    image_url: "https://storage.googleapis.com/falserverless/example_inputs/hunyuan_i2v.jpg"
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

- [Model Playground](https://fal.ai/models/nvidia/cosmos-3-super/image-to-video)
- [API Documentation](https://fal.ai/models/nvidia/cosmos-3-super/image-to-video/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=nvidia/cosmos-3-super/image-to-video)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
