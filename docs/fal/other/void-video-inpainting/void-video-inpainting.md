# Void Video Inpainting

> VOID removes objects from videos along with all interactions they induce on the scene


## Overview

- **Endpoint**: `https://fal.run/fal-ai/void-video-inpainting`
- **Model ID**: `fal-ai/void-video-inpainting`
- **Category**: video-to-video
- **Kind**: inference
**Tags**: utility, editing



## Pricing

Your request will cost **$0.05** per **video**. With Pass2 enabled it will cost **$0.1** per **video**. Sam3 quad mask generation will cost an additional **$0.05**.

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`video_url`** (`string`, _required_):
  URL of the input video containing the object to remove.
  - Examples: "https://storage.googleapis.com/falserverless/kontext-blog/input_video.mp4"

- **`quad_mask_video_url`** (`string`, _optional_):
  URL of a mask video for the removal target. For best results this should be a VOID-style quadmask video with 4 grayscale values: 0=object to remove, 63=overlap, 127=affected region, 255=background to keep. A simple binary mask (0=remove, 255=keep) also works. If omitted, the app will generate a temporary mask video from `mask_prompt` using the SAM-3 video endpoint and convert it to a quadmask automatically. Default value: `""`
  - Default: `""`
  - Examples: "https://storage.googleapis.com/falserverless/kontext-blog/trimask_quadmask.mp4"

- **`mask_prompt`** (`string`, _optional_):
  Text description of what should be masked in the input video, such as the object or person to remove. Used to generate a temporary mask video with SAM-3 when `quad_mask_video_url` is not provided.
  - Examples: "the person walking through the hallway"

- **`prompt`** (`string`, _required_):
  Text description of the desired background after object removal.
  - Examples: "a video of buildings reflecting on a calm river"

- **`enable_pass2_refinement`** (`boolean`, _optional_):
  Run VOID Pass 2 warped-noise refinement after Pass 1. This is slower but can improve temporal consistency on longer clips.
  - Default: `false`

- **`negative_prompt`** (`string`, _optional_):
  Negative prompt to guide generation away from undesired outputs. Default value: `"The video is not of a high quality, it has a low resolution. Watermark present in each frame. The background is solid. Strange body and strange trajectory. Distortion."`
  - Default: `"The video is not of a high quality, it has a low resolution. Watermark present in each frame. The background is solid. Strange body and strange trajectory. Distortion."`

- **`num_inference_steps`** (`integer`, _optional_):
  Number of denoising steps. Higher values improve quality but increase latency. Default value: `30`
  - Default: `30`
  - Range: `1` to `50`

- **`guidance_scale`** (`float`, _optional_):
  Classifier-free guidance scale. Default value: `1`
  - Default: `1`
  - Range: `0` to `20`

- **`strength`** (`float`, _optional_):
  Denoising strength. 1.0 means full denoising. Default value: `1`
  - Default: `1`
  - Range: `0` to `1`

- **`seed`** (`integer`, _optional_):
  Random seed for reproducibility.

- **`num_frames`** (`integer`, _optional_):
  Temporal window size for inference. The backend snaps this to the nearest CogVideoX-safe value that works with temporal compression and patching. Valid outputs are 69, 77, 85, ..., 197. Default value: `85`
  - Default: `85`
  - Range: `1` to `197`

- **`enable_safety_checker`** (`boolean`, _optional_):
  Enable content safety checking on the output. Default value: `true`
  - Default: `true`



**Required Parameters Example**:

```json
{
  "video_url": "https://storage.googleapis.com/falserverless/kontext-blog/input_video.mp4",
  "prompt": "a video of buildings reflecting on a calm river"
}
```

**Full Example**:

```json
{
  "video_url": "https://storage.googleapis.com/falserverless/kontext-blog/input_video.mp4",
  "quad_mask_video_url": "https://storage.googleapis.com/falserverless/kontext-blog/trimask_quadmask.mp4",
  "mask_prompt": "the person walking through the hallway",
  "prompt": "a video of buildings reflecting on a calm river",
  "negative_prompt": "The video is not of a high quality, it has a low resolution. Watermark present in each frame. The background is solid. Strange body and strange trajectory. Distortion.",
  "num_inference_steps": 30,
  "guidance_scale": 1,
  "strength": 1,
  "num_frames": 85,
  "enable_safety_checker": true
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`File`, _required_):
  The output video with the object removed.
  - Examples: {"url":"https://v3b.fal.media/files/b/0a95b6f4/D89J5QV-wztq3B0OI44Sl_tmpl1cf522v.mp4"}

- **`seed`** (`integer`, _required_):
  The seed used for generation.

- **`timings`** (`Timings`, _required_):
  Timing breakdown for pipeline stages.



**Example Response**:

```json
{
  "video": {
    "url": "https://v3b.fal.media/files/b/0a95b6f4/D89J5QV-wztq3B0OI44Sl_tmpl1cf522v.mp4"
  }
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/void-video-inpainting \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "video_url": "https://storage.googleapis.com/falserverless/kontext-blog/input_video.mp4",
     "prompt": "a video of buildings reflecting on a calm river"
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
    "fal-ai/void-video-inpainting",
    arguments={
        "video_url": "https://storage.googleapis.com/falserverless/kontext-blog/input_video.mp4",
        "prompt": "a video of buildings reflecting on a calm river"
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

const result = await fal.subscribe("fal-ai/void-video-inpainting", {
  input: {
    video_url: "https://storage.googleapis.com/falserverless/kontext-blog/input_video.mp4",
    prompt: "a video of buildings reflecting on a calm river"
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

- [Model Playground](https://fal.ai/models/fal-ai/void-video-inpainting)
- [API Documentation](https://fal.ai/models/fal-ai/void-video-inpainting/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/void-video-inpainting)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
