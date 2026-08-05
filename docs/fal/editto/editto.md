# Editto

> Edit videos using instruction-based prompting using Editto model!


## Overview

- **Endpoint**: `https://fal.run/fal-ai/editto`
- **Model ID**: `fal-ai/editto`
- **Category**: video-to-video
- **Kind**: inference
**Tags**: video-edit, wan-vace



## Pricing

Your request will cost **$0.08** per **video second** for **720p**, **$0.06** per **video second** for **580p**, **$0.04** per **video second** for **480p**. Video seconds are calculated at 16 frames per second.

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _required_):
  The text prompt to guide video generation.
  - Examples: "Make it a Pixel Art video."

- **`negative_prompt`** (`string`, _optional_):
  Negative prompt for video generation. Default value: `"letterboxing, borders, black bars, bright colors, overexposed, static, blurred details, subtitles, style, artwork, painting, picture, still, overall gray, worst quality, low quality, JPEG compression residue, ugly, incomplete, extra fingers, poorly drawn hands, poorly drawn faces, deformed, disfigured, malformed limbs, fused fingers, still picture, cluttered background, three legs, many people in the background, walking backwards"`
  - Default: `"letterboxing, borders, black bars, bright colors, overexposed, static, blurred details, subtitles, style, artwork, painting, picture, still, overall gray, worst quality, low quality, JPEG compression residue, ugly, incomplete, extra fingers, poorly drawn hands, poorly drawn faces, deformed, disfigured, malformed limbs, fused fingers, still picture, cluttered background, three legs, many people in the background, walking backwards"`
  - Examples: "色调艳丽，过曝，静态，细节模糊不清，字幕，风格，作品，画作，画面，静止，整体发灰，最差质量，低质量，JPEG压缩残留，丑陋的，残缺的，多余的手指，画得不好的手部，画得不好的脸部，畸形的，毁容的，形态畸形的肢体，手指融合，静止不动的画面，杂乱的背景，三条腿，背景人很多，倒着走"

- **`match_input_num_frames`** (`boolean`, _optional_):
  If true, the number of frames in the generated video will match the number of frames in the input video. If false, the number of frames will be determined by the num_frames parameter.
  - Default: `false`
  - Examples: true

- **`num_frames`** (`integer`, _optional_):
  Number of frames to generate. Must be between 81 to 241 (inclusive). Default value: `81`
  - Default: `81`
  - Range: `17` to `241`

- **`match_input_frames_per_second`** (`boolean`, _optional_):
  If true, the frames per second of the generated video will match the input video. If false, the frames per second will be determined by the frames_per_second parameter.
  - Default: `false`
  - Examples: true

- **`frames_per_second`** (`integer`, _optional_):
  Frames per second of the generated video. Must be between 5 to 30. Ignored if match_input_frames_per_second is true. Default value: `16`
  - Default: `16`
  - Range: `5` to `30`

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
  - Examples: 50

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
  URL to the source video file. Required for inpainting.
  - Examples: "https://storage.googleapis.com/falserverless/example_inputs/editto/example_in.mp4"

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

- **`num_interpolated_frames`** (`integer`, _optional_):
  Number of frames to interpolate between the original frames. A value of 0 means no interpolation.
  - Default: `0`
  - Range: `0` to `5`
  - Examples: 0

- **`temporal_downsample_factor`** (`integer`, _optional_):
  Temporal downsample factor for the video. This is an integer value that determines how many frames to skip in the video. A value of 0 means no downsampling. For each downsample factor, one upsample factor will automatically be applied.
  - Default: `0`
  - Range: `0` to `5`
  - Examples: 0

- **`enable_auto_downsample`** (`boolean`, _optional_):
  If true, the model will automatically temporally downsample the video to an appropriate frame length for the model, then will interpolate it back to the original frame length.
  - Default: `false`
  - Examples: false

- **`sync_mode`** (`boolean`, _optional_):
  If `True`, the media will be returned as a data URI and the output data won't be available in the request history.
  - Default: `false`
  - Examples: false

- **`return_frames_zip`** (`boolean`, _optional_):
  If true, also return a ZIP file containing all generated frames.
  - Default: `false`
  - Examples: false



**Required Parameters Example**:

```json
{
  "prompt": "Make it a Pixel Art video.",
  "video_url": "https://storage.googleapis.com/falserverless/example_inputs/editto/example_in.mp4"
}
```

**Full Example**:

```json
{
  "prompt": "Make it a Pixel Art video.",
  "negative_prompt": "色调艳丽，过曝，静态，细节模糊不清，字幕，风格，作品，画作，画面，静止，整体发灰，最差质量，低质量，JPEG压缩残留，丑陋的，残缺的，多余的手指，画得不好的手部，画得不好的脸部，畸形的，毁容的，形态畸形的肢体，手指融合，静止不动的画面，杂乱的背景，三条腿，背景人很多，倒着走",
  "match_input_num_frames": true,
  "num_frames": 81,
  "match_input_frames_per_second": true,
  "frames_per_second": 16,
  "resolution": "auto",
  "aspect_ratio": "auto",
  "num_inference_steps": 50,
  "guidance_scale": 5,
  "sampler": "unipc",
  "shift": 5,
  "video_url": "https://storage.googleapis.com/falserverless/example_inputs/editto/example_in.mp4",
  "enable_safety_checker": true,
  "acceleration": "regular",
  "video_quality": "high",
  "video_write_mode": "balanced",
  "num_interpolated_frames": 0,
  "temporal_downsample_factor": 0,
  "enable_auto_downsample": false,
  "sync_mode": false,
  "return_frames_zip": false
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`VideoFile`, _required_):
  The generated image to video file.
  - Examples: {"file_name":"example_out.mp4","url":"https://storage.googleapis.com/falserverless/example_outputs/editto/example_out.mp4","num_frames":73,"height":480,"width":832,"fps":15,"duration":4.86,"content_type":"video/mp4"}

- **`prompt`** (`string`, _required_):
  The prompt used for generation.
  - Examples: "Make it a Pixel Art video."

- **`seed`** (`integer`, _required_):
  The seed used for generation.
  - Examples: 1096772785

- **`frames_zip`** (`File`, _optional_):
  ZIP archive of all video frames if requested.



**Example Response**:

```json
{
  "video": {
    "file_name": "example_out.mp4",
    "url": "https://storage.googleapis.com/falserverless/example_outputs/editto/example_out.mp4",
    "num_frames": 73,
    "height": 480,
    "width": 832,
    "fps": 15,
    "duration": 4.86,
    "content_type": "video/mp4"
  },
  "prompt": "Make it a Pixel Art video.",
  "seed": 1096772785
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/editto \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "Make it a Pixel Art video.",
     "video_url": "https://storage.googleapis.com/falserverless/example_inputs/editto/example_in.mp4"
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
    "fal-ai/editto",
    arguments={
        "prompt": "Make it a Pixel Art video.",
        "video_url": "https://storage.googleapis.com/falserverless/example_inputs/editto/example_in.mp4"
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

const result = await fal.subscribe("fal-ai/editto", {
  input: {
    prompt: "Make it a Pixel Art video.",
    video_url: "https://storage.googleapis.com/falserverless/example_inputs/editto/example_in.mp4"
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

- [Model Playground](https://fal.ai/models/fal-ai/editto)
- [API Documentation](https://fal.ai/models/fal-ai/editto/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/editto)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
