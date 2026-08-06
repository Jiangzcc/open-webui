# Ltx 2.3 Quality

> Transform your 3D video render into realistic using first frame with Ltx 2.3


## Overview

- **Endpoint**: `https://fal.run/fal-ai/ltx-2.3-quality/render-to-real`
- **Model ID**: `fal-ai/ltx-2.3-quality/render-to-real`
- **Category**: video-to-video
- **Kind**: inference
**Tags**: 3d, video, 



## Pricing

Your request will cost **$0.0024075** per megapixel of generated video data (width × height × frames), rounded up. For example, if you generate a video that is 121 frames long at 1280 × 720, your total generated video is ≈112 MP, and your request will cost **$0.270**. If you turn on **enable_detail_refine**, the output is delivered at 2× the width AND 2× the height — that is **4× the pixels, so roughly 4× the price**: the same 121 frames delivered at 2560 × 1440 are ≈447 MP, and your request will cost **$1.076**.

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`video_url`** (`string`, _required_):
  The URL of the 3D / CG / game render to make photorealistic.
  - Examples: "https://v3b.fal.media/files/b/0a8824b1/sdm0KfmenrlywesfzY1Y1_if6euPp1.mp4"

- **`image_url`** (`string`, _optional_):
  Optional reference image used as the FIRST frame (image-to-video anchor), matching how the adapter was trained. It defines the photoreal look of frame 0; leave empty to let the render alone drive the result.

- **`intensity`** (`IntensityEnum`, _optional_):
  How hard to push the render toward photorealism. 'light' keeps more of the source render's look and motion; 'strong' transforms more aggressively for a more photoreal result; 'strong-v2' is the newest improved adapter (better multi-scene coherence, audio, talking characters, and higher overall quality). Default value: `"light"`
  - Default: `"light"`
  - Options: `"light"`, `"strong"`, `"strong-v2"`

- **`enable_detail_refine`** (`boolean`, _optional_):
  Add a second refinement stage for a sharper, higher-resolution result. After the base pass the video latent is 2x latent-upscaled (spatial upscaler) and refined by a short detailer pass on the distilled model. NOTE: this doubles the output width AND height (4x the pixels), so the request costs roughly 4X THE PRICE and is slower. Off by default.
  - Default: `false`

- **`detail_refine_strength`** (`float`, _optional_):
  Denoise strength of the detailer pass, used only when enable_detail_refine is on. Higher regenerates more detail (and can drift further from the base); lower is a lighter touch that stays closer to the base. Default 0.75. Default value: `0.75`
  - Default: `0.75`
  - Range: `0.3` to `0.95`

- **`prompt`** (`string`, _optional_):
  The text prompt, pre-filled with the `3DREAL` trigger the adapter activates on. Describe the photorealistic result after it. The `3DREAL` trigger is always kept, even if you clear it or enable prompt expansion. Default value: `"3DREAL. "`
  - Default: `"3DREAL. "`
  - Examples: "3DREAL. Make it a detailed realistic 3D render. A sleek, futuristic hoverbike with glowing blue lights speeds down a multi-lane highway, leaving a trail of orange exhaust."

- **`resolution`** (`ResolutionEnum`, _optional_):
  Output resolution (short side), preserving the source aspect ratio. The IC-LoRA control path caps the resolution x frames volume, so resolution trades against duration: 720p allows up to ~6s (sharper), 480p up to ~15s (softer but longer). A request above the budget is rejected with a clear error — pick 480p for longer clips. Output duration is num_frames / frames_per_second. Default value: `"720p"`
  - Default: `"720p"`
  - Options: `"480p"`, `"720p"`

- **`num_frames`** (`integer`, _optional_):
  The number of output frames. Output duration is num_frames / frames_per_second. The IC-LoRA control budget caps the resolution x frames volume: roughly 6s at 720p or 15s at 480p; a request above it returns a 422 (lower num_frames, or use 480p). Default value: `121`
  - Default: `121`
  - Range: `9` to `481`

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

- **`enable_prompt_expansion`** (`boolean`, _optional_):
  When enabled, an AI model expands your prompt into a richer description before generation (off by default sends it as written). The `3DREAL` trigger is always kept, and the final prompt used is returned in the output.
  - Default: `false`

- **`seed`** (`integer`, _optional_):
  Random seed for reproducibility. If None, a random seed is chosen.

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
  "video_url": "https://v3b.fal.media/files/b/0a8824b1/sdm0KfmenrlywesfzY1Y1_if6euPp1.mp4"
}
```

**Full Example**:

```json
{
  "video_url": "https://v3b.fal.media/files/b/0a8824b1/sdm0KfmenrlywesfzY1Y1_if6euPp1.mp4",
  "intensity": "light",
  "detail_refine_strength": 0.75,
  "prompt": "3DREAL. Make it a detailed realistic 3D render. A sleek, futuristic hoverbike with glowing blue lights speeds down a multi-lane highway, leaving a trail of orange exhaust.",
  "resolution": "720p",
  "num_frames": 121,
  "frames_per_second": 24,
  "num_inference_steps": 15,
  "guidance_scale": 1,
  "generate_audio": true,
  "negative_prompt": "color distortion, overexposure, static, blurry details, subtitles, style, artwork, painting, frame, still, dim overall tone, worst quality, low quality, JPEG compression artifacts, ugly, mutilated, extra fingers, poorly drawn hands, poorly drawn face, deformed, disfigured, malformed limbs, fused fingers, motionless frame, cluttered background, three legs, crowded background, walking backwards",
  "enable_safety_checker": true,
  "video_quality": "high",
  "video_write_mode": "balanced"
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`File`, _required_):
  The generated video.

- **`seed`** (`integer`, _required_):
  The seed actually used for generation.

- **`prompt`** (`string`, _required_):
  The prompt used for generation (after any expansion).



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
  --url https://fal.run/fal-ai/ltx-2.3-quality/render-to-real \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
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
    "fal-ai/ltx-2.3-quality/render-to-real",
    arguments={
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

const result = await fal.subscribe("fal-ai/ltx-2.3-quality/render-to-real", {
  input: {
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

- [Model Playground](https://fal.ai/models/fal-ai/ltx-2.3-quality/render-to-real)
- [API Documentation](https://fal.ai/models/fal-ai/ltx-2.3-quality/render-to-real/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/ltx-2.3-quality/render-to-real)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
