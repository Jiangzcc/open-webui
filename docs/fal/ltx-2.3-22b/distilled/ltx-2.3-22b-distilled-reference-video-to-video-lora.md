# LTX-2.3 22B Distilled

> Generate video with audio from reference videos using LTX-2.3 Distilled and custom LoRA


## Overview

- **Endpoint**: `https://fal.run/fal-ai/ltx-2.3-22b/distilled/reference-video-to-video/lora`
- **Model ID**: `fal-ai/ltx-2.3-22b/distilled/reference-video-to-video/lora`
- **Category**: video-to-video
- **Kind**: inference


## Pricing

Your request will cost $0.001405 per megapixel of generated video data (width × height × frames), rounded up. For example, if you generate a video that is 121 frames long at 1280 × 720, your total generated video is ≈112 MP, and your request will cost $0.1567.

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _required_):
  The prompt to generate the video from.
  - Examples: "style: cinematic/realistic. A man wearing a baseball cap walks through a modern town. He holds a coffee cup."

- **`video_url`** (`string`, _required_):
  The URL of the video to reference.
  - Examples: "https://v3b.fal.media/files/b/0a963ecf/eVoII1AsconU8SpPx5xoE_output.mp4"

- **`audio_url`** (`string`, _optional_):
  An optional URL of an audio to use as the audio for the video. If not provided, any audio present in the input video will be used.

- **`image_url`** (`string`, _optional_):
  An optional URL of an image to use as the first frame of the video.

- **`end_image_url`** (`string`, _optional_):
  The URL of the image to use as the end of the video.

- **`match_video_length`** (`boolean`, _optional_):
  When enabled, the number of frames will be calculated based on the video duration and FPS. When disabled, use the specified num_frames. Default value: `true`
  - Default: `true`

- **`num_frames`** (`integer`, _optional_):
  The number of frames to generate. Default value: `121`
  - Default: `121`
  - Range: `9` to `481`

- **`video_size`** (`ImageSize | Enum`, _optional_):
  The size of the generated video. Default value: `auto`
  - Default: `"auto"`
  - One of: ImageSize | Enum

- **`generate_audio`** (`boolean`, _optional_):
  Whether to generate audio for the video. Default value: `true`
  - Default: `true`

- **`use_multiscale`** (`boolean`, _optional_):
  Whether to use multi-scale generation. If True, the model will generate the video at a smaller scale first, then use the smaller video to guide the generation of a video at or above your requested size. This results in better coherence and details. Default value: `true`
  - Default: `true`

- **`match_input_fps`** (`boolean`, _optional_):
  When true, match the output FPS to the input video's FPS instead of using the default target FPS. Default value: `true`
  - Default: `true`

- **`fps`** (`float`, _optional_):
  The frames per second of the generated video. Default value: `24`
  - Default: `24`
  - Range: `1` to `60`

- **`scheduler`** (`SchedulerEnum`, _optional_):
  The scheduler to use. Default value: `"ltx2"`
  - Default: `"ltx2"`
  - Options: `"ltx2"`, `"linear_quadratic"`, `"beta"`
  - Examples: "ltx2"

- **`acceleration`** (`AccelerationEnum`, _optional_):
  The acceleration level to use. Default value: `"none"`
  - Default: `"none"`
  - Options: `"none"`, `"regular"`, `"high"`, `"full"`
  - Examples: "none"

- **`camera_lora`** (`CameraLoRAEnum`, _optional_):
  The camera LoRA to use. This allows you to control the camera movement of the generated video more accurately than just prompting the model to move the camera. Default value: `"none"`
  - Default: `"none"`
  - Options: `"dolly_in"`, `"dolly_out"`, `"dolly_left"`, `"dolly_right"`, `"jib_up"`, `"jib_down"`, `"static"`, `"none"`
  - Examples: "none"

- **`camera_lora_scale`** (`float`, _optional_):
  The scale of the camera LoRA to use. This allows you to control the camera movement of the generated video more accurately than just prompting the model to move the camera. Default value: `1`
  - Default: `1`
  - Range: `0` to `1`

- **`negative_prompt`** (`string`, _optional_):
  The negative prompt to generate the video from. Default value: `"news broadcast, 3d animation, computer graphics, pc game, console game, video game, cartoon, childish, watermark, logo, text, on screen text, subtitles, titles, signature, slowmo, static"`
  - Default: `"news broadcast, 3d animation, computer graphics, pc game, console game, video game, cartoon, childish, watermark, logo, text, on screen text, subtitles, titles, signature, slowmo, static"`

- **`seed`** (`integer`, _optional_):
  The seed for the random number generator.

- **`enable_prompt_expansion`** (`boolean`, _optional_):
  Whether to enable prompt expansion. Default value: `true`
  - Default: `true`

- **`enable_safety_checker`** (`boolean`, _optional_):
  Whether to enable the safety checker. Default value: `true`
  - Default: `true`

- **`video_output_type`** (`VideoOutputTypeEnum`, _optional_):
  The output type of the generated video. Default value: `"X264 (.mp4)"`
  - Default: `"X264 (.mp4)"`
  - Options: `"X264 (.mp4)"`, `"VP9 (.webm)"`, `"PRORES4444 (.mov)"`, `"GIF (.gif)"`

- **`video_quality`** (`VideoQualityEnum`, _optional_):
  The quality of the generated video. Default value: `"high"`
  - Default: `"high"`
  - Options: `"low"`, `"medium"`, `"high"`, `"maximum"`

- **`video_write_mode`** (`VideoWriteModeEnum`, _optional_):
  The write mode of the generated video. Default value: `"balanced"`
  - Default: `"balanced"`
  - Options: `"fast"`, `"balanced"`, `"small"`

- **`sync_mode`** (`boolean`, _optional_):
  If `True`, the media will be returned as a data URI and the output data won't be available in the request history.
  - Default: `false`

- **`loras`** (`list<LoRAInput>`, _required_):
  The LoRAs to use for the generation.
  - Array of LoRAInput

- **`distill_lora_second_pass_scale`** (`float`, _optional_):
  The scale of the distill LoRA to use for the second and subsequent passes. Default value: `0.5`
  - Default: `0.5`
  - Range: `0` to `1`

- **`video_strength`** (`float`, _optional_):
  Video conditioning strength. Lower values represent more freedom given to the model to change the video content. Default value: `1`
  - Default: `1`
  - Range: `0` to `1`

- **`audio_strength`** (`float`, _optional_):
  Audio conditioning strength. Lower values represent more freedom given to the model to change the audio content. Default value: `1`
  - Default: `1`
  - Range: `0` to `1`

- **`preprocessor`** (`PreprocessorEnum`, _optional_):
  The preprocessor to use for the generation. Default value: `"none"`
  - Default: `"none"`
  - Options: `"depth"`, `"canny"`, `"pose"`, `"none"`

- **`ic_lora_type`** (`IC-LoRATypeEnum`, _optional_):
  The IC LoRA type to use for the generation. Default value: `"union"`
  - Default: `"union"`
  - Options: `"match_preprocessor"`, `"union"`, `"detailer"`, `"none"`
  - Examples: "union"



**Required Parameters Example**:

```json
{
  "prompt": "style: cinematic/realistic. A man wearing a baseball cap walks through a modern town. He holds a coffee cup.",
  "video_url": "https://v3b.fal.media/files/b/0a963ecf/eVoII1AsconU8SpPx5xoE_output.mp4",
  "loras": [
    {
      "path": "",
      "scale": 1
    }
  ]
}
```

**Full Example**:

```json
{
  "prompt": "style: cinematic/realistic. A man wearing a baseball cap walks through a modern town. He holds a coffee cup.",
  "video_url": "https://v3b.fal.media/files/b/0a963ecf/eVoII1AsconU8SpPx5xoE_output.mp4",
  "match_video_length": true,
  "num_frames": 121,
  "video_size": "auto",
  "generate_audio": true,
  "use_multiscale": true,
  "match_input_fps": true,
  "fps": 24,
  "scheduler": "ltx2",
  "acceleration": "none",
  "camera_lora": "none",
  "camera_lora_scale": 1,
  "negative_prompt": "news broadcast, 3d animation, computer graphics, pc game, console game, video game, cartoon, childish, watermark, logo, text, on screen text, subtitles, titles, signature, slowmo, static",
  "enable_prompt_expansion": true,
  "enable_safety_checker": true,
  "video_output_type": "X264 (.mp4)",
  "video_quality": "high",
  "video_write_mode": "balanced",
  "loras": [
    {
      "path": "",
      "scale": 1
    }
  ],
  "distill_lora_second_pass_scale": 0.5,
  "video_strength": 1,
  "audio_strength": 1,
  "preprocessor": "none",
  "ic_lora_type": "union"
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`VideoFile`, _required_):
  The generated video.
  - Examples: {"width":1888,"duration":6.44,"height":1056,"fps":25,"content_type":"video/mp4","url":"https://v3b.fal.media/files/b/0a9640bb/vqhmP1B5juujIXfBPTotm_5MBoh7yS.mp4","file_name":"vqhmP1B5juujIXfBPTotm_5MBoh7yS.mp4","num_frames":161}

- **`seed`** (`integer`, _required_):
  The seed used for the random number generator.
  - Examples: 1490631192028410600

- **`prompt`** (`string`, _required_):
  The prompt used for the generation.
  - Examples: "black-and-white video, a cowboy walks through a dusty town, film grain"



**Example Response**:

```json
{
  "video": {
    "width": 1888,
    "duration": 6.44,
    "height": 1056,
    "fps": 25,
    "content_type": "video/mp4",
    "url": "https://v3b.fal.media/files/b/0a9640bb/vqhmP1B5juujIXfBPTotm_5MBoh7yS.mp4",
    "file_name": "vqhmP1B5juujIXfBPTotm_5MBoh7yS.mp4",
    "num_frames": 161
  },
  "seed": 1490631192028410600,
  "prompt": "black-and-white video, a cowboy walks through a dusty town, film grain"
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/ltx-2.3-22b/distilled/reference-video-to-video/lora \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "style: cinematic/realistic. A man wearing a baseball cap walks through a modern town. He holds a coffee cup.",
     "video_url": "https://v3b.fal.media/files/b/0a963ecf/eVoII1AsconU8SpPx5xoE_output.mp4",
     "loras": [
       {
         "path": "",
         "scale": 1
       }
     ]
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
    "fal-ai/ltx-2.3-22b/distilled/reference-video-to-video/lora",
    arguments={
        "prompt": "style: cinematic/realistic. A man wearing a baseball cap walks through a modern town. He holds a coffee cup.",
        "video_url": "https://v3b.fal.media/files/b/0a963ecf/eVoII1AsconU8SpPx5xoE_output.mp4",
        "loras": [{
            "path": "",
            "scale": 1
        }]
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

const result = await fal.subscribe("fal-ai/ltx-2.3-22b/distilled/reference-video-to-video/lora", {
  input: {
    prompt: "style: cinematic/realistic. A man wearing a baseball cap walks through a modern town. He holds a coffee cup.",
    video_url: "https://v3b.fal.media/files/b/0a963ecf/eVoII1AsconU8SpPx5xoE_output.mp4",
    loras: [{
      path: "",
      scale: 1
    }]
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

- [Model Playground](https://fal.ai/models/fal-ai/ltx-2.3-22b/distilled/reference-video-to-video/lora)
- [API Documentation](https://fal.ai/models/fal-ai/ltx-2.3-22b/distilled/reference-video-to-video/lora/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/ltx-2.3-22b/distilled/reference-video-to-video/lora)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
