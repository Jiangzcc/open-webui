# Wan 2.1 VACE Long Reframe

> Reframe entire videos scene-by-scene using Wan VACE 2.1


## Overview

- **Endpoint**: `https://fal.run/fal-ai/wan-vace-apps/long-reframe`
- **Model ID**: `fal-ai/wan-vace-apps/long-reframe`
- **Category**: video-to-video
- **Kind**: inference


## Pricing

Your request will cost **$0.08** per **2 seconds of output video** for **720p**, **$0.06** per **2 seconds of output video** for **580p**, abd **$0.04** per **2 seconds of output video** for **480p**. Seconds are rounded up to the nearest multiple of 2.

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _optional_):
  The text prompt to guide video generation. Optional for reframing. Default value: `""`
  - Default: `""`
  - Examples: ""

- **`negative_prompt`** (`string`, _optional_):
  Negative prompt for video generation. Default value: `"letterboxing, borders, black bars, bright colors, overexposed, static, blurred details, subtitles, style, artwork, painting, picture, still, overall gray, worst quality, low quality, JPEG compression residue, ugly, incomplete, extra fingers, poorly drawn hands, poorly drawn faces, deformed, disfigured, malformed limbs, fused fingers, still picture, cluttered background, three legs, many people in the background, walking backwards"`
  - Default: `"letterboxing, borders, black bars, bright colors, overexposed, static, blurred details, subtitles, style, artwork, painting, picture, still, overall gray, worst quality, low quality, JPEG compression residue, ugly, incomplete, extra fingers, poorly drawn hands, poorly drawn faces, deformed, disfigured, malformed limbs, fused fingers, still picture, cluttered background, three legs, many people in the background, walking backwards"`
  - Examples: "letterboxing, borders, black bars, bright colors, overexposed, static, blurred details, subtitles, style, artwork, painting, picture, still, overall gray, worst quality, low quality, JPEG compression residue, ugly, incomplete, extra fingers, poorly drawn hands, poorly drawn faces, deformed, disfigured, malformed limbs, fused fingers, still picture, cluttered background, three legs, many people in the background, walking backwards"

- **`seed`** (`integer`, _optional_):
  Random seed for reproducibility. If None, a random seed is chosen.

- **`resolution`** (`ResolutionEnum`, _optional_):
  Resolution of the generated video. Default value: `"auto"`
  - Default: `"auto"`
  - Options: `"auto"`, `"240p"`, `"360p"`, `"480p"`, `"580p"`, `"720p"`

- **`aspect_ratio`** (`AspectRatioEnum`, _optional_):
  Aspect ratio of the generated video. Default value: `"auto"`
  - Default: `"auto"`
  - Options: `"auto"`, `"16:9"`, `"1:1"`, `"9:16"`

- **`num_inference_steps`** (`integer`, _optional_):
  Number of inference steps for sampling. Higher values give better quality but take longer. Default value: `30`
  - Default: `30`
  - Range: `2` to `50`

- **`guidance_scale`** (`float`, _optional_):
  Guidance scale for classifier-free guidance. Higher values encourage the model to generate images closely related to the text prompt. Default value: `5`
  - Default: `5`
  - Range: `1` to `10`
  - Examples: 5

- **`sampler`** (`SamplerEnum`, _optional_):
  Sampler to use for video generation. Default value: `"unipc"`
  - Default: `"unipc"`
  - Options: `"unipc"`, `"dpm++"`, `"euler"`
  - Examples: "unipc"

- **`shift`** (`float`, _optional_):
  Shift parameter for video generation. Default value: `5`
  - Default: `5`
  - Range: `1` to `15`

- **`video_url`** (`string`, _required_):
  URL to the source video file. This video will be used as a reference for the reframe task.
  - Examples: "https://storage.googleapis.com/falserverless/web-examples/wan/t2v.mp4"

- **`enable_safety_checker`** (`boolean`, _optional_):
  If set to true, the safety checker will be enabled.
  - Default: `false`
  - Examples: true

- **`acceleration`** (`Enum`, _optional_):
  Acceleration to use for inference. Options are 'none' or 'regular'. Accelerated inference will very slightly affect output, but will be significantly faster. Default value: `regular`
  - Default: `"regular"`
  - Options: `"none"`, `"low"`, `"regular"`
  - Examples: "regular"

- **`video_quality`** (`VideoQualityEnum`, _optional_):
  The quality of the generated video. Default value: `"high"`
  - Default: `"high"`
  - Options: `"low"`, `"medium"`, `"high"`, `"maximum"`
  - Examples: "high"

- **`video_write_mode`** (`VideoWriteModeEnum`, _optional_):
  The write mode of the generated video. Default value: `"balanced"`
  - Default: `"balanced"`
  - Options: `"fast"`, `"balanced"`, `"small"`
  - Examples: "balanced"

- **`enable_auto_downsample`** (`boolean`, _optional_):
  Whether to enable auto downsample. Default value: `true`
  - Default: `true`
  - Examples: true

- **`auto_downsample_min_fps`** (`float`, _optional_):
  Minimum FPS for auto downsample. Default value: `6`
  - Default: `6`
  - Range: `1` to `60`
  - Examples: 6

- **`interpolator_model`** (`InterpolatorModelEnum`, _optional_):
  The model to use for frame interpolation. Options are 'rife' or 'film'. Default value: `"film"`
  - Default: `"film"`
  - Options: `"rife"`, `"film"`
  - Examples: "film"

- **`sync_mode`** (`boolean`, _optional_):
  If `True`, the media will be returned as a data URI and the output data won't be available in the request history.
  - Default: `false`
  - Examples: false

- **`transparency_mode`** (`TransparencyModeEnum`, _optional_):
  The transparency mode to apply to the first and last frames. This controls how the transparent areas of the first and last frames are filled. Default value: `"content_aware"`
  - Default: `"content_aware"`
  - Options: `"content_aware"`, `"white"`, `"black"`
  - Examples: "content_aware"

- **`return_frames_zip`** (`boolean`, _optional_):
  If true, also return a ZIP file containing all generated frames.
  - Default: `false`
  - Examples: false

- **`zoom_factor`** (`float`, _optional_):
  Zoom factor for the video. When this value is greater than 0, the video will be zoomed in by this factor (in relation to the canvas size,) cutting off the edges of the video. A value of 0 means no zoom.
  - Default: `0`
  - Range: `0` to `0.9`
  - Examples: 0

- **`trim_borders`** (`boolean`, _optional_):
  Whether to trim borders from the video. Default value: `true`
  - Default: `true`
  - Examples: true

- **`scene_threshold`** (`float`, _optional_):
  Threshold for scene detection sensitivity (0-100). Lower values detect more scenes. Default value: `30`
  - Default: `30`
  - Range: `0` to `100`

- **`paste_back`** (`boolean`, _optional_):
  Whether to paste back the reframed scene to the original video. Default value: `true`
  - Default: `true`



**Required Parameters Example**:

```json
{
  "video_url": "https://storage.googleapis.com/falserverless/web-examples/wan/t2v.mp4"
}
```

**Full Example**:

```json
{
  "prompt": "",
  "negative_prompt": "letterboxing, borders, black bars, bright colors, overexposed, static, blurred details, subtitles, style, artwork, painting, picture, still, overall gray, worst quality, low quality, JPEG compression residue, ugly, incomplete, extra fingers, poorly drawn hands, poorly drawn faces, deformed, disfigured, malformed limbs, fused fingers, still picture, cluttered background, three legs, many people in the background, walking backwards",
  "resolution": "auto",
  "aspect_ratio": "auto",
  "num_inference_steps": 30,
  "guidance_scale": 5,
  "sampler": "unipc",
  "shift": 5,
  "video_url": "https://storage.googleapis.com/falserverless/web-examples/wan/t2v.mp4",
  "enable_safety_checker": true,
  "acceleration": "regular",
  "video_quality": "high",
  "video_write_mode": "balanced",
  "enable_auto_downsample": true,
  "auto_downsample_min_fps": 6,
  "interpolator_model": "film",
  "sync_mode": false,
  "transparency_mode": "content_aware",
  "return_frames_zip": false,
  "zoom_factor": 0,
  "trim_borders": true,
  "scene_threshold": 30,
  "paste_back": true
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`VideoFile`, _required_):
  The output video file.



**Example Response**:

```json
{
  "video": {
    "url": "",
    "content_type": "image/png",
    "file_name": "z9RV14K95DvU.png",
    "file_size": 4404019
  }
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/wan-vace-apps/long-reframe \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "video_url": "https://storage.googleapis.com/falserverless/web-examples/wan/t2v.mp4"
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
    "fal-ai/wan-vace-apps/long-reframe",
    arguments={
        "video_url": "https://storage.googleapis.com/falserverless/web-examples/wan/t2v.mp4"
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

const result = await fal.subscribe("fal-ai/wan-vace-apps/long-reframe", {
  input: {
    video_url: "https://storage.googleapis.com/falserverless/web-examples/wan/t2v.mp4"
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

- [Model Playground](https://fal.ai/models/fal-ai/wan-vace-apps/long-reframe)
- [API Documentation](https://fal.ai/models/fal-ai/wan-vace-apps/long-reframe/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/wan-vace-apps/long-reframe)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
