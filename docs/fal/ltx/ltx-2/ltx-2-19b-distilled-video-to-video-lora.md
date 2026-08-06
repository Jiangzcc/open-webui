# LTX-2 19B Distilled

> Generate video with audio from videos using LTX-2 Distilled and custom LoRA


## Overview

- **Endpoint**: `https://fal.run/fal-ai/ltx-2-19b/distilled/video-to-video/lora`
- **Model ID**: `fal-ai/ltx-2-19b/distilled/video-to-video/lora`
- **Category**: video-to-video
- **Kind**: inference


## Pricing

Your request will cost $0.001 per megapixel of generated video data (width × height × frames), rounded up. For example, if you generate a video that is 121 frames long at 1280 × 720, your total generated video is ≈112 MP, and your request will cost $0.112.

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _required_):
  The prompt to generate the video from.
  - Examples: "black-and-white video, a cowboy walks through a dusty town, film grain"

- **`video_url`** (`string`, _required_):
  The URL of the video to generate the video from.
  - Examples: "https://v3b.fal.media/files/b/0a8824b1/sdm0KfmenrlywesfzY1Y1_if6euPp1.mp4"

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
  The frames per second of the generated video. Default value: `25`
  - Default: `25`
  - Range: `1` to `60`

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
  The negative prompt to generate the video from. Default value: `"blurry, out of focus, overexposed, underexposed, low contrast, washed out colors, excessive noise, grainy texture, poor lighting, flickering, motion blur, distorted proportions, unnatural skin tones, deformed facial features, asymmetrical face, missing facial features, extra limbs, disfigured hands, wrong hand count, artifacts around text, inconsistent perspective, camera shake, incorrect depth of field, background too sharp, background clutter, distracting reflections, harsh shadows, inconsistent lighting direction, color banding, cartoonish rendering, 3D CGI look, unrealistic materials, uncanny valley effect, incorrect ethnicity, wrong gender, exaggerated expressions, wrong gaze direction, mismatched lip sync, silent or muted audio, distorted voice, robotic voice, echo, background noise, off-sync audio,incorrect dialogue, added dialogue, repetitive speech, jittery movement, awkward pauses, incorrect timing, unnatural transitions, inconsistent framing, tilted camera, flat lighting, inconsistent tone, cinematic oversaturation, stylized filters, or AI artifacts."`
  - Default: `"blurry, out of focus, overexposed, underexposed, low contrast, washed out colors, excessive noise, grainy texture, poor lighting, flickering, motion blur, distorted proportions, unnatural skin tones, deformed facial features, asymmetrical face, missing facial features, extra limbs, disfigured hands, wrong hand count, artifacts around text, inconsistent perspective, camera shake, incorrect depth of field, background too sharp, background clutter, distracting reflections, harsh shadows, inconsistent lighting direction, color banding, cartoonish rendering, 3D CGI look, unrealistic materials, uncanny valley effect, incorrect ethnicity, wrong gender, exaggerated expressions, wrong gaze direction, mismatched lip sync, silent or muted audio, distorted voice, robotic voice, echo, background noise, off-sync audio,incorrect dialogue, added dialogue, repetitive speech, jittery movement, awkward pauses, incorrect timing, unnatural transitions, inconsistent framing, tilted camera, flat lighting, inconsistent tone, cinematic oversaturation, stylized filters, or AI artifacts."`

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

- **`preprocessor`** (`PreprocessorEnum`, _optional_):
  The preprocessor to use for the video. When a preprocessor is used and `ic_lora_type` is set to `match_preprocessor`, the IC-LoRA will be loaded based on the preprocessor type. Default value: `"none"`
  - Default: `"none"`
  - Options: `"depth"`, `"canny"`, `"pose"`, `"none"`
  - Examples: "none"

- **`ic_lora`** (`IC-LoRAEnum`, _optional_):
  The type of IC-LoRA to load. In-Context LoRA weights are used to condition the video based on edge, depth, or pose videos. Only change this from `match_preprocessor` if your videos are already preprocessed (or you are using the detailer.) Default value: `"match_preprocessor"`
  - Default: `"match_preprocessor"`
  - Options: `"match_preprocessor"`, `"canny"`, `"depth"`, `"pose"`, `"detailer"`, `"none"`
  - Examples: "match_preprocessor"

- **`ic_lora_scale`** (`float`, _optional_):
  The scale of the IC-LoRA to use. This allows you to control the strength of the IC-LoRA. Default value: `1`
  - Default: `1`
  - Range: `0` to `1`

- **`image_strength`** (`float`, _optional_):
  The strength of the image to use for the video generation. Default value: `1`
  - Default: `1`
  - Range: `0` to `1`

- **`end_image_strength`** (`float`, _optional_):
  The strength of the end image to use for the video generation. Default value: `1`
  - Default: `1`
  - Range: `0` to `1`

- **`video_strength`** (`float`, _optional_):
  Video conditioning strength. Lower values represent more freedom given to the model to change the video content. Default value: `1`
  - Default: `1`
  - Range: `0` to `1`

- **`audio_strength`** (`float`, _optional_):
  Audio conditioning strength. Lower values represent more freedom given to the model to change the audio content. Default value: `1`
  - Default: `1`
  - Range: `0` to `1`



**Required Parameters Example**:

```json
{
  "prompt": "black-and-white video, a cowboy walks through a dusty town, film grain",
  "video_url": "https://v3b.fal.media/files/b/0a8824b1/sdm0KfmenrlywesfzY1Y1_if6euPp1.mp4",
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
  "prompt": "black-and-white video, a cowboy walks through a dusty town, film grain",
  "video_url": "https://v3b.fal.media/files/b/0a8824b1/sdm0KfmenrlywesfzY1Y1_if6euPp1.mp4",
  "match_video_length": true,
  "num_frames": 121,
  "video_size": "auto",
  "generate_audio": true,
  "use_multiscale": true,
  "match_input_fps": true,
  "fps": 25,
  "acceleration": "none",
  "camera_lora": "none",
  "camera_lora_scale": 1,
  "negative_prompt": "blurry, out of focus, overexposed, underexposed, low contrast, washed out colors, excessive noise, grainy texture, poor lighting, flickering, motion blur, distorted proportions, unnatural skin tones, deformed facial features, asymmetrical face, missing facial features, extra limbs, disfigured hands, wrong hand count, artifacts around text, inconsistent perspective, camera shake, incorrect depth of field, background too sharp, background clutter, distracting reflections, harsh shadows, inconsistent lighting direction, color banding, cartoonish rendering, 3D CGI look, unrealistic materials, uncanny valley effect, incorrect ethnicity, wrong gender, exaggerated expressions, wrong gaze direction, mismatched lip sync, silent or muted audio, distorted voice, robotic voice, echo, background noise, off-sync audio,incorrect dialogue, added dialogue, repetitive speech, jittery movement, awkward pauses, incorrect timing, unnatural transitions, inconsistent framing, tilted camera, flat lighting, inconsistent tone, cinematic oversaturation, stylized filters, or AI artifacts.",
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
  "preprocessor": "none",
  "ic_lora": "match_preprocessor",
  "ic_lora_scale": 1,
  "image_strength": 1,
  "end_image_strength": 1,
  "video_strength": 1,
  "audio_strength": 1
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`VideoFile`, _required_):
  The generated video.
  - Examples: {"num_frames":161,"height":704,"fps":25,"url":"https://v3b.fal.media/files/b/0a895ed5/SaTGe87IpMUMiSq33w5Qb_RoCJFZhc.mp4","duration":6.44,"file_name":"SaTGe87IpMUMiSq33w5Qb_RoCJFZhc.mp4","content_type":"video/mp4","width":1248}

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
    "num_frames": 161,
    "height": 704,
    "fps": 25,
    "url": "https://v3b.fal.media/files/b/0a895ed5/SaTGe87IpMUMiSq33w5Qb_RoCJFZhc.mp4",
    "duration": 6.44,
    "file_name": "SaTGe87IpMUMiSq33w5Qb_RoCJFZhc.mp4",
    "content_type": "video/mp4",
    "width": 1248
  },
  "seed": 1490631192028410600,
  "prompt": "black-and-white video, a cowboy walks through a dusty town, film grain"
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/ltx-2-19b/distilled/video-to-video/lora \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "black-and-white video, a cowboy walks through a dusty town, film grain",
     "video_url": "https://v3b.fal.media/files/b/0a8824b1/sdm0KfmenrlywesfzY1Y1_if6euPp1.mp4",
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
    "fal-ai/ltx-2-19b/distilled/video-to-video/lora",
    arguments={
        "prompt": "black-and-white video, a cowboy walks through a dusty town, film grain",
        "video_url": "https://v3b.fal.media/files/b/0a8824b1/sdm0KfmenrlywesfzY1Y1_if6euPp1.mp4",
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

const result = await fal.subscribe("fal-ai/ltx-2-19b/distilled/video-to-video/lora", {
  input: {
    prompt: "black-and-white video, a cowboy walks through a dusty town, film grain",
    video_url: "https://v3b.fal.media/files/b/0a8824b1/sdm0KfmenrlywesfzY1Y1_if6euPp1.mp4",
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

- [Model Playground](https://fal.ai/models/fal-ai/ltx-2-19b/distilled/video-to-video/lora)
- [API Documentation](https://fal.ai/models/fal-ai/ltx-2-19b/distilled/video-to-video/lora/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/ltx-2-19b/distilled/video-to-video/lora)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
