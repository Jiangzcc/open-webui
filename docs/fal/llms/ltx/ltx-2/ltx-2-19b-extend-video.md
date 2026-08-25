# LTX-2 19B

> Extend video with audio using LTX-2


## Overview

- **Endpoint**: `https://fal.run/fal-ai/ltx-2-19b/extend-video`
- **Model ID**: `fal-ai/ltx-2-19b/extend-video`
- **Category**: video-to-video
- **Kind**: inference


## Pricing

- **Price**: $0.0018 per megapixels

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _required_):
  The prompt to generate the video from.
  - Examples: "Continue the scene naturally, maintaining the same style and motion."

- **`video_url`** (`string`, _required_):
  The URL of the video to extend.
  - Examples: "https://v3b.fal.media/files/b/0a8824b1/sdm0KfmenrlywesfzY1Y1_if6euPp1.mp4"

- **`end_image_url`** (`string`, _optional_):
  The URL of the image to use as the end of the extended video.

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

- **`guidance_scale`** (`float`, _optional_):
  The guidance scale to use. Default value: `3`
  - Default: `3`
  - Range: `1` to `10`

- **`num_inference_steps`** (`integer`, _optional_):
  The number of inference steps to use. Default value: `40`
  - Default: `40`
  - Range: `8` to `50`

- **`acceleration`** (`AccelerationEnum`, _optional_):
  The acceleration level to use. Default value: `"regular"`
  - Default: `"regular"`
  - Options: `"none"`, `"regular"`, `"high"`, `"full"`
  - Examples: "regular"

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

- **`extend_direction`** (`ExtendDirectionEnum`, _optional_):
  Direction to extend the video. 'forward' extends from the end of the video, 'backward' extends from the beginning. Default value: `"forward"`
  - Default: `"forward"`
  - Options: `"forward"`, `"backward"`

- **`num_context_frames`** (`integer`, _optional_):
  The number of frames to use as context for the extension. Default value: `25`
  - Default: `25`
  - Range: `0` to `121`

- **`video_strength`** (`float`, _optional_):
  Video conditioning strength. Lower values represent more freedom given to the model to change the video content. Default value: `1`
  - Default: `1`
  - Range: `0` to `1`

- **`audio_strength`** (`float`, _optional_):
  Audio conditioning strength. Lower values represent more freedom given to the model to change the audio content. Default value: `1`
  - Default: `1`
  - Range: `0` to `1`

- **`end_image_strength`** (`float`, _optional_):
  The strength of the end image to use for the video generation. Default value: `1`
  - Default: `1`
  - Range: `0` to `1`



**Required Parameters Example**:

```json
{
  "prompt": "Continue the scene naturally, maintaining the same style and motion.",
  "video_url": "https://v3b.fal.media/files/b/0a8824b1/sdm0KfmenrlywesfzY1Y1_if6euPp1.mp4"
}
```

**Full Example**:

```json
{
  "prompt": "Continue the scene naturally, maintaining the same style and motion.",
  "video_url": "https://v3b.fal.media/files/b/0a8824b1/sdm0KfmenrlywesfzY1Y1_if6euPp1.mp4",
  "num_frames": 121,
  "video_size": "auto",
  "generate_audio": true,
  "use_multiscale": true,
  "match_input_fps": true,
  "fps": 25,
  "guidance_scale": 3,
  "num_inference_steps": 40,
  "acceleration": "regular",
  "camera_lora": "none",
  "camera_lora_scale": 1,
  "negative_prompt": "blurry, out of focus, overexposed, underexposed, low contrast, washed out colors, excessive noise, grainy texture, poor lighting, flickering, motion blur, distorted proportions, unnatural skin tones, deformed facial features, asymmetrical face, missing facial features, extra limbs, disfigured hands, wrong hand count, artifacts around text, inconsistent perspective, camera shake, incorrect depth of field, background too sharp, background clutter, distracting reflections, harsh shadows, inconsistent lighting direction, color banding, cartoonish rendering, 3D CGI look, unrealistic materials, uncanny valley effect, incorrect ethnicity, wrong gender, exaggerated expressions, wrong gaze direction, mismatched lip sync, silent or muted audio, distorted voice, robotic voice, echo, background noise, off-sync audio,incorrect dialogue, added dialogue, repetitive speech, jittery movement, awkward pauses, incorrect timing, unnatural transitions, inconsistent framing, tilted camera, flat lighting, inconsistent tone, cinematic oversaturation, stylized filters, or AI artifacts.",
  "enable_prompt_expansion": true,
  "enable_safety_checker": true,
  "video_output_type": "X264 (.mp4)",
  "video_quality": "high",
  "video_write_mode": "balanced",
  "extend_direction": "forward",
  "num_context_frames": 25,
  "video_strength": 1,
  "audio_strength": 1,
  "end_image_strength": 1
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`VideoFile`, _required_):
  The generated video.
  - Examples: {"num_frames":161,"height":704,"fps":25,"url":"https://v3b.fal.media/files/b/0a894013/N9lnMTq7W3uMC0lOQg845_BknRPV8I.mp4","duration":6.44,"file_name":"CJcQGDrxOSRg2YFl5GNDt_glXPMoji.mp4","content_type":"video/mp4","width":1248}

- **`seed`** (`integer`, _required_):
  The seed used for the random number generator.
  - Examples: 2078003885

- **`prompt`** (`string`, _required_):
  The prompt used for the generation.
  - Examples: "A woman stands still amid a busy neon-lit street at night. The camera slowly dollies in toward her face as people blur past, their motion emphasizing her calm presence. City lights flicker and reflections shift across her denim jacket."



**Example Response**:

```json
{
  "video": {
    "num_frames": 161,
    "height": 704,
    "fps": 25,
    "url": "https://v3b.fal.media/files/b/0a894013/N9lnMTq7W3uMC0lOQg845_BknRPV8I.mp4",
    "duration": 6.44,
    "file_name": "CJcQGDrxOSRg2YFl5GNDt_glXPMoji.mp4",
    "content_type": "video/mp4",
    "width": 1248
  },
  "seed": 2078003885,
  "prompt": "A woman stands still amid a busy neon-lit street at night. The camera slowly dollies in toward her face as people blur past, their motion emphasizing her calm presence. City lights flicker and reflections shift across her denim jacket."
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/ltx-2-19b/extend-video \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "Continue the scene naturally, maintaining the same style and motion.",
     "video_url": "https://v3b.fal.media/files/b/0a8824b1/sdm0KfmenrlywesfzY1Y1_if6euPp1.mp4"
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
    "fal-ai/ltx-2-19b/extend-video",
    arguments={
        "prompt": "Continue the scene naturally, maintaining the same style and motion.",
        "video_url": "https://v3b.fal.media/files/b/0a8824b1/sdm0KfmenrlywesfzY1Y1_if6euPp1.mp4"
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

const result = await fal.subscribe("fal-ai/ltx-2-19b/extend-video", {
  input: {
    prompt: "Continue the scene naturally, maintaining the same style and motion.",
    video_url: "https://v3b.fal.media/files/b/0a8824b1/sdm0KfmenrlywesfzY1Y1_if6euPp1.mp4"
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

- [Model Playground](https://fal.ai/models/fal-ai/ltx-2-19b/extend-video)
- [API Documentation](https://fal.ai/models/fal-ai/ltx-2-19b/extend-video/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/ltx-2-19b/extend-video)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
