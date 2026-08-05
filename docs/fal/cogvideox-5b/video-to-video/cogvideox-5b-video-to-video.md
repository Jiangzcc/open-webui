# CogVideoX-5B

> Generate videos from videos and prompts using CogVideoX-5B


## Overview

- **Endpoint**: `https://fal.run/fal-ai/cogvideox-5b/video-to-video`
- **Model ID**: `fal-ai/cogvideox-5b/video-to-video`
- **Category**: video-to-video
- **Kind**: inference
**Tags**: editing



## Pricing

- **Price**: $0.2 per videos

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _required_):
  The prompt to generate the video from.
  - Examples: "An astronaut stands triumphantly at the peak of a towering mountain. Panorama of rugged peaks and valleys. Very futuristic vibe and animated aesthetic. Highlights of purple and golden colors in the scene. The sky is looks like an animated/cartoonish dream of galaxies, nebulae, stars, planets, moons, but the remainder of the scene is mostly realistic. "

- **`video_size`** (`ImageSize | Enum`, _optional_):
  The size of the generated video.
  - Default: `{"width":720,"height":480}`
  - One of: ImageSize | Enum

- **`negative_prompt`** (`string`, _optional_):
  The negative prompt to generate video from Default value: `""`
  - Default: `""`
  - Examples: "Distorted, discontinuous, Ugly, blurry, low resolution, motionless, static, disfigured, disconnected limbs, Ugly faces, incomplete arms"

- **`loras`** (`list<LoraWeight>`, _optional_):
  The LoRAs to use for the image generation. We currently support one lora.
  - Default: `[]`
  - Array of LoraWeight

- **`num_inference_steps`** (`integer`, _optional_):
  The number of inference steps to perform. Default value: `50`
  - Default: `50`
  - Range: `1` to `50`

- **`seed`** (`integer`, _optional_):
  The same seed and the same prompt given to the same version of the model
  will output the same video every time.

- **`guidance_scale`** (`float`, _optional_):
  The CFG (Classifier Free Guidance) scale is a measure of how close you want
  the model to stick to your prompt when looking for a related video to show you. Default value: `7`
  - Default: `7`
  - Range: `0` to `20`

- **`use_rife`** (`boolean`, _optional_):
  Use RIFE for video interpolation Default value: `true`
  - Default: `true`

- **`export_fps`** (`integer`, _optional_):
  The target FPS of the video Default value: `16`
  - Default: `16`
  - Range: `4` to `32`

- **`video_url`** (`string`, _required_):
  The video to generate the video from.
  - Examples: "https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/diffusers/hiker.mp4"

- **`strength`** (`float`, _optional_):
  The strength to use for Video to Video.  1.0 completely remakes the video while 0.0 preserves the original. Default value: `0.8`
  - Default: `0.8`
  - Range: `0.05` to `1`



**Required Parameters Example**:

```json
{
  "prompt": "An astronaut stands triumphantly at the peak of a towering mountain. Panorama of rugged peaks and valleys. Very futuristic vibe and animated aesthetic. Highlights of purple and golden colors in the scene. The sky is looks like an animated/cartoonish dream of galaxies, nebulae, stars, planets, moons, but the remainder of the scene is mostly realistic. ",
  "video_url": "https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/diffusers/hiker.mp4"
}
```

**Full Example**:

```json
{
  "prompt": "An astronaut stands triumphantly at the peak of a towering mountain. Panorama of rugged peaks and valleys. Very futuristic vibe and animated aesthetic. Highlights of purple and golden colors in the scene. The sky is looks like an animated/cartoonish dream of galaxies, nebulae, stars, planets, moons, but the remainder of the scene is mostly realistic. ",
  "video_size": {
    "width": 720,
    "height": 480
  },
  "negative_prompt": "Distorted, discontinuous, Ugly, blurry, low resolution, motionless, static, disfigured, disconnected limbs, Ugly faces, incomplete arms",
  "num_inference_steps": 50,
  "guidance_scale": 7,
  "use_rife": true,
  "export_fps": 16,
  "video_url": "https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/diffusers/hiker.mp4",
  "strength": 0.8
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`File`, _required_):
  The URL to the generated video

- **`timings`** (`Timings`, _required_)

- **`seed`** (`integer`, _required_):
  Seed of the generated video. It will be the same value of the one passed in the
  input or the randomly generated that was used in case none was passed.

- **`prompt`** (`string`, _required_):
  The prompt used for generating the video.



**Example Response**:

```json
{
  "video": {
    "url": "",
    "content_type": "image/png",
    "file_name": "z9RV14K95DvU.png",
    "file_size": 4404019
  },
  "prompt": ""
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/cogvideox-5b/video-to-video \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "An astronaut stands triumphantly at the peak of a towering mountain. Panorama of rugged peaks and valleys. Very futuristic vibe and animated aesthetic. Highlights of purple and golden colors in the scene. The sky is looks like an animated/cartoonish dream of galaxies, nebulae, stars, planets, moons, but the remainder of the scene is mostly realistic. ",
     "video_url": "https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/diffusers/hiker.mp4"
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
    "fal-ai/cogvideox-5b/video-to-video",
    arguments={
        "prompt": "An astronaut stands triumphantly at the peak of a towering mountain. Panorama of rugged peaks and valleys. Very futuristic vibe and animated aesthetic. Highlights of purple and golden colors in the scene. The sky is looks like an animated/cartoonish dream of galaxies, nebulae, stars, planets, moons, but the remainder of the scene is mostly realistic. ",
        "video_url": "https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/diffusers/hiker.mp4"
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

const result = await fal.subscribe("fal-ai/cogvideox-5b/video-to-video", {
  input: {
    prompt: "An astronaut stands triumphantly at the peak of a towering mountain. Panorama of rugged peaks and valleys. Very futuristic vibe and animated aesthetic. Highlights of purple and golden colors in the scene. The sky is looks like an animated/cartoonish dream of galaxies, nebulae, stars, planets, moons, but the remainder of the scene is mostly realistic. ",
    video_url: "https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/diffusers/hiker.mp4"
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

- [Model Playground](https://fal.ai/models/fal-ai/cogvideox-5b/video-to-video)
- [API Documentation](https://fal.ai/models/fal-ai/cogvideox-5b/video-to-video/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/cogvideox-5b/video-to-video)
- [GitHub Repository](https://huggingface.co/THUDM/CogVideoX-5b/blob/main/LICENSE)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
