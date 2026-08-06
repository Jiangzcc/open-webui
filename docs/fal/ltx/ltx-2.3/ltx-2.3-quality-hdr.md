# Ltx 2.3 Quality

> Generate HDR from reference video using LTX-2.3 


## Overview

- **Endpoint**: `https://fal.run/fal-ai/ltx-2.3-quality/hdr`
- **Model ID**: `fal-ai/ltx-2.3-quality/hdr`
- **Category**: video-to-video
- **Kind**: inference


## Pricing

Your request will cost $0.0027075 per megapixel of generated HDR video data (width × height × frames), rounded up. For example, if you generate 121 HDR frames at 1280 × 720, your total generated output is ≈112 MP, and your request will cost $0.3032.

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _required_):
  The prompt to guide generation.
  - Examples: "A sunset over the Pacific Ocean, vibrant orange and purple sky, deep contrast, cinematic HDR."

- **`video_url`** (`string`, _required_):
  SDR input video to lift into HDR. This mode is video-conditioned.

- **`num_frames`** (`integer`, _optional_):
  The number of frames to generate. Default value: `121`
  - Default: `121`
  - Range: `9` to `481`

- **`resolution`** (`ImageSize | Enum`, _optional_):
  Output video size. The output is generated at up to ~720p (shorter side capped at 704px); larger requested sizes are scaled down, preserving the aspect ratio. Default value: `auto`
  - Default: `"auto"`
  - One of: ImageSize | Enum

- **`frames_per_second`** (`float`, _optional_):
  Frames per second of the generated video. Default value: `24`
  - Default: `24`
  - Range: `1` to `60`

- **`num_inference_steps`** (`integer`, _optional_):
  Number of inference steps. Defaults to 15 and can be increased up to 30. Default value: `15`
  - Default: `15`
  - Range: `8` to `30`

- **`guidance_scale`** (`float`, _optional_):
  Classifier-free guidance scale. The default is tuned for fast, high-quality generation. Default value: `1`
  - Default: `1`
  - Range: `1` to `20`

- **`generate_audio`** (`boolean`, _optional_):
  Whether to include audio in the returned video. When disabled, the final MP4 is returned without an audio track. Default value: `true`
  - Default: `true`

- **`negative_prompt`** (`string`, _optional_):
  The negative prompt to steer generation away from. Default value: `"color distortion, overexposure, static, blurry details, subtitles, style, artwork, painting, frame, still, dim overall tone, worst quality, low quality, JPEG compression artifacts, ugly, mutilated, extra fingers, poorly drawn hands, poorly drawn face, deformed, disfigured, malformed limbs, fused fingers, motionless frame, cluttered background, three legs, crowded background, walking backwards"`
  - Default: `"color distortion, overexposure, static, blurry details, subtitles, style, artwork, painting, frame, still, dim overall tone, worst quality, low quality, JPEG compression artifacts, ugly, mutilated, extra fingers, poorly drawn hands, poorly drawn face, deformed, disfigured, malformed limbs, fused fingers, motionless frame, cluttered background, three legs, crowded background, walking backwards"`

- **`seed`** (`integer`, _optional_):
  Random seed for reproducibility. If None, a random seed is chosen.

- **`enable_prompt_expansion`** (`boolean`, _optional_):
  Whether to enable prompt expansion. Default value: `true`
  - Default: `true`

- **`enable_safety_checker`** (`boolean`, _optional_):
  Whether to enable the safety checker. Default value: `true`
  - Default: `true`

- **`video_quality`** (`VideoQualityEnum`, _optional_):
  The quality preset of the generated video. Default value: `"high"`
  - Default: `"high"`
  - Options: `"low"`, `"medium"`, `"high"`, `"maximum"`

- **`video_write_mode`** (`VideoWriteModeEnum`, _optional_):
  The write mode of the generated video. Default value: `"balanced"`
  - Default: `"balanced"`
  - Options: `"fast"`, `"balanced"`, `"small"`

- **`sync_mode`** (`boolean`, _optional_):
  If True, the media is returned as a data URI inline in the response. Useful for short-lived requests and tests.
  - Default: `false`



**Required Parameters Example**:

```json
{
  "prompt": "A sunset over the Pacific Ocean, vibrant orange and purple sky, deep contrast, cinematic HDR.",
  "video_url": ""
}
```

**Full Example**:

```json
{
  "prompt": "A sunset over the Pacific Ocean, vibrant orange and purple sky, deep contrast, cinematic HDR.",
  "video_url": "",
  "num_frames": 121,
  "resolution": "auto",
  "frames_per_second": 24,
  "num_inference_steps": 15,
  "guidance_scale": 1,
  "generate_audio": true,
  "negative_prompt": "color distortion, overexposure, static, blurry details, subtitles, style, artwork, painting, frame, still, dim overall tone, worst quality, low quality, JPEG compression artifacts, ugly, mutilated, extra fingers, poorly drawn hands, poorly drawn face, deformed, disfigured, malformed limbs, fused fingers, motionless frame, cluttered background, three legs, crowded background, walking backwards",
  "enable_prompt_expansion": true,
  "enable_safety_checker": true,
  "video_quality": "high",
  "video_write_mode": "balanced"
}
```


### Output Schema

The API returns the following output format:

- **`preview_video`** (`VideoFile`, _required_):
  MP4 preview of the HDR result for quick inspection.

- **`exr_frames_url`** (`File`, _required_):
  ZIP archive containing one 16-bit EXR frame per output frame.

- **`seed`** (`integer`, _required_):
  The seed actually used for generation.

- **`prompt`** (`string`, _required_):
  The prompt used for generation (after any expansion).



**Example Response**:

```json
{
  "preview_video": {
    "url": "",
    "content_type": "image/png",
    "file_name": "z9RV14K95DvU.png",
    "file_size": 4404019
  },
  "exr_frames_url": {
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
  --url https://fal.run/fal-ai/ltx-2.3-quality/hdr \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "A sunset over the Pacific Ocean, vibrant orange and purple sky, deep contrast, cinematic HDR.",
     "video_url": ""
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
    "fal-ai/ltx-2.3-quality/hdr",
    arguments={
        "prompt": "A sunset over the Pacific Ocean, vibrant orange and purple sky, deep contrast, cinematic HDR.",
        "video_url": ""
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

const result = await fal.subscribe("fal-ai/ltx-2.3-quality/hdr", {
  input: {
    prompt: "A sunset over the Pacific Ocean, vibrant orange and purple sky, deep contrast, cinematic HDR.",
    video_url: ""
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

- [Model Playground](https://fal.ai/models/fal-ai/ltx-2.3-quality/hdr)
- [API Documentation](https://fal.ai/models/fal-ai/ltx-2.3-quality/hdr/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/ltx-2.3-quality/hdr)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
