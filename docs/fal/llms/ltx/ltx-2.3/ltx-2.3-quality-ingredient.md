# Ltx 2.3 Quality

> Generate high-quality video with audio from reference, character sheet, storyboard using LTX-2.3


## Overview

- **Endpoint**: `https://fal.run/fal-ai/ltx-2.3-quality/ingredient`
- **Model ID**: `fal-ai/ltx-2.3-quality/ingredient`
- **Category**: image-to-video
- **Kind**: inference
**Tags**: ingredient, storyboard, video



## Pricing

Your request will cost **$0.0024075** per megapixel of generated video data (width × height × frames), rounded up. For example, if you generate a video that is 121 frames long at 1280 × 720, your total generated video is ≈112 MP, and your request will cost **$0.270.**

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _required_):
  The prompt to guide the generated video. For best results, use a 'Reference sheet: ... Generated video: ...' structure.
  - Examples: "Reference sheet: a chef in a white jacket, a copper pan, fresh basil, and a bright studio kitchen. Generated video: the chef tosses pasta in the copper pan, steam rising, cinematic food commercial."

- **`image_url`** (`string`, _required_):
  URL of the Ingredient reference sheet image. The sheet should contain clean panels for the characters, props, and location to preserve.
  - Examples: "https://storage.googleapis.com/falserverless/example_inputs/ltxv-2-i2v-input.jpg"

- **`num_frames`** (`integer`, _optional_):
  The number of frames to generate. Default value: `121`
  - Default: `121`
  - Range: `9` to `481`

- **`resolution`** (`ImageSize | Enum`, _optional_):
  The final generated video size. The default keeps the workflow's first stage at the Ingredient LoRA's trained 768x448 bucket before the official 2x refinement stage.
  - Default: `{"height":896,"width":1536}`
  - One of: ImageSize | Enum

- **`frames_per_second`** (`float`, _optional_):
  Frames per second of the generated video. Default value: `24`
  - Default: `24`
  - Range: `1` to `60`

- **`guidance_scale`** (`float`, _optional_):
  Classifier-free guidance scale. Default value: `1`
  - Default: `1`
  - Range: `1` to `20`

- **`ingredient_strength`** (`float`, _optional_):
  Strength of the built-in Ingredient IC-LoRA. Higher values make the reference sheet identities and props more dominant. Default value: `1`
  - Default: `1`
  - Range: `0` to `2`

- **`reference_strength`** (`float`, _optional_):
  Strength of the reference-sheet guide. 1.0 uses the sheet fully; lower values give the model more freedom. Default value: `1`
  - Default: `1`
  - Range: `0` to `2`

- **`generate_audio`** (`boolean`, _optional_):
  Whether to include audio in the returned video. When disabled, the final MP4 is returned without an audio track. Default value: `true`
  - Default: `true`

- **`negative_prompt`** (`string`, _optional_):
  The negative prompt to steer generation away from. Default value: `"worst quality, inconsistent motion, blurry, jittery, distorted"`
  - Default: `"worst quality, inconsistent motion, blurry, jittery, distorted"`

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
  "prompt": "Reference sheet: a chef in a white jacket, a copper pan, fresh basil, and a bright studio kitchen. Generated video: the chef tosses pasta in the copper pan, steam rising, cinematic food commercial.",
  "image_url": "https://storage.googleapis.com/falserverless/example_inputs/ltxv-2-i2v-input.jpg"
}
```

**Full Example**:

```json
{
  "prompt": "Reference sheet: a chef in a white jacket, a copper pan, fresh basil, and a bright studio kitchen. Generated video: the chef tosses pasta in the copper pan, steam rising, cinematic food commercial.",
  "image_url": "https://storage.googleapis.com/falserverless/example_inputs/ltxv-2-i2v-input.jpg",
  "num_frames": 121,
  "resolution": {
    "height": 896,
    "width": 1536
  },
  "frames_per_second": 24,
  "guidance_scale": 1,
  "ingredient_strength": 1,
  "reference_strength": 1,
  "generate_audio": true,
  "negative_prompt": "worst quality, inconsistent motion, blurry, jittery, distorted",
  "enable_prompt_expansion": true,
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
  --url https://fal.run/fal-ai/ltx-2.3-quality/ingredient \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "Reference sheet: a chef in a white jacket, a copper pan, fresh basil, and a bright studio kitchen. Generated video: the chef tosses pasta in the copper pan, steam rising, cinematic food commercial.",
     "image_url": "https://storage.googleapis.com/falserverless/example_inputs/ltxv-2-i2v-input.jpg"
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
    "fal-ai/ltx-2.3-quality/ingredient",
    arguments={
        "prompt": "Reference sheet: a chef in a white jacket, a copper pan, fresh basil, and a bright studio kitchen. Generated video: the chef tosses pasta in the copper pan, steam rising, cinematic food commercial.",
        "image_url": "https://storage.googleapis.com/falserverless/example_inputs/ltxv-2-i2v-input.jpg"
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

const result = await fal.subscribe("fal-ai/ltx-2.3-quality/ingredient", {
  input: {
    prompt: "Reference sheet: a chef in a white jacket, a copper pan, fresh basil, and a bright studio kitchen. Generated video: the chef tosses pasta in the copper pan, steam rising, cinematic food commercial.",
    image_url: "https://storage.googleapis.com/falserverless/example_inputs/ltxv-2-i2v-input.jpg"
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

- [Model Playground](https://fal.ai/models/fal-ai/ltx-2.3-quality/ingredient)
- [API Documentation](https://fal.ai/models/fal-ai/ltx-2.3-quality/ingredient/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/ltx-2.3-quality/ingredient)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
