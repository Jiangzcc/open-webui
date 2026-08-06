# Scail 2

> SCAIL-2 is an end-to-end character animation model that drives a reference character from a source video without relying on intermediate pose representations like skeleton maps. 


## Overview

- **Endpoint**: `https://fal.run/fal-ai/scail-2`
- **Model ID**: `fal-ai/scail-2`
- **Category**: video-to-video
- **Kind**: inference
**Tags**: stylized, transform



## Pricing

SCAIL-2 is billed per second of generated video at a flat rate of **$0.20 per second**, the same for both output resolutions (512p and 704p).

Generated video is always produced at 16 fps, so billed seconds = total output frames ÷ 16 — which is simply the duration of the output video in seconds.

**How your cost is calculated:**

1. Billed seconds = output duration (total frames ÷ 16 fps)
2. Cost = billed seconds × $0.20

**Example — 5-second output:** 5 × $0.20 = **$1.00**

Each request is capped at 10 seconds of video (160 frames at 16 fps), so the maximum cost per request is **$2.00**.

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _required_):
  The prompt describing the final video to generate.
  - Examples: "A person dancing gracefully in a sunlit studio"

- **`image_url`** (`string`, _required_):
  URL of the reference character image. The character in this image is animated (or used to replace a subject) according to the driving video.
  - Examples: "https://v3b.fal.media/files/b/panda/-oMlZo9Yyj_Nzoza_tgds_GmLF86r5bOt50eMMKCszy_eacc949b3933443c9915a83c98fbe85e.png"

- **`video_url`** (`string`, _required_):
  URL of the driving (motion) video. The subject can be a human, multiple humans, or an animal.
  - Examples: "https://v3b.fal.media/files/b/panda/a6SvJg96V8eoglMlYFShU_5385885-hd_1080_1920_25fps.mp4"

- **`mode`** (`ModeEnum`, _optional_):
  `animation` animates the reference character with the driving motion. `replacement` replaces the driving subject with the reference character while keeping the original scene. Default value: `"animation"`
  - Default: `"animation"`
  - Options: `"animation"`, `"replacement"`

- **`driving_type`** (`DrivingTypeEnum`, _optional_):
  Driving signal for animation mode. `end_to_end` (default) drives directly from the SAM3-masked driving video and is the recommended, most robust path. `pose` renders an explicit NLF/DWPose skeleton from the driving video (more control for challenging inputs). Default value: `"end_to_end"`
  - Default: `"end_to_end"`
  - Options: `"end_to_end"`, `"pose"`

- **`subject_type`** (`SubjectTypeEnum`, _optional_):
  Type of subject in the driving video. `animal` switches the SAM3 detection prompt to non-human subjects. Default value: `"human"`
  - Default: `"human"`
  - Options: `"human"`, `"animal"`

- **`resolution`** (`ResolutionEnum`, _optional_):
  Output resolution. 512p outputs 896x512 (landscape) or 512x896 (portrait); 704p outputs 1280x704 or 704x1280. Orientation is chosen automatically from the reference image aspect ratio. Default value: `"512p"`
  - Default: `"512p"`
  - Options: `"512p"`, `"704p"`

- **`num_inference_steps`** (`integer`, _optional_):
  Number of diffusion sampling steps. Higher improves quality but is slower. Default value: `40`
  - Default: `40`
  - Range: `2` to `50`

- **`guidance_scale`** (`float`, _optional_):
  Classifier-free guidance scale. Controls prompt adherence versus creativity. Default value: `5`
  - Default: `5`
  - Range: `1` to `10`

- **`shift`** (`float`, _optional_):
  Flow-matching noise schedule shift. 3.0 is recommended for the 512p tier. Default value: `3`
  - Default: `3`
  - Range: `1` to `10`

- **`seed`** (`integer`, _optional_):
  Random seed. Leave empty for a random seed. The seed used is returned in the response.



**Required Parameters Example**:

```json
{
  "prompt": "A person dancing gracefully in a sunlit studio",
  "image_url": "https://v3b.fal.media/files/b/panda/-oMlZo9Yyj_Nzoza_tgds_GmLF86r5bOt50eMMKCszy_eacc949b3933443c9915a83c98fbe85e.png",
  "video_url": "https://v3b.fal.media/files/b/panda/a6SvJg96V8eoglMlYFShU_5385885-hd_1080_1920_25fps.mp4"
}
```

**Full Example**:

```json
{
  "prompt": "A person dancing gracefully in a sunlit studio",
  "image_url": "https://v3b.fal.media/files/b/panda/-oMlZo9Yyj_Nzoza_tgds_GmLF86r5bOt50eMMKCszy_eacc949b3933443c9915a83c98fbe85e.png",
  "video_url": "https://v3b.fal.media/files/b/panda/a6SvJg96V8eoglMlYFShU_5385885-hd_1080_1920_25fps.mp4",
  "mode": "animation",
  "driving_type": "end_to_end",
  "subject_type": "human",
  "resolution": "512p",
  "num_inference_steps": 40,
  "guidance_scale": 5,
  "shift": 3
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`File`, _required_):
  The generated video file.
  - Examples: {"file_name":"output.mp4","url":"https://storage.googleapis.com/falserverless/example_outputs/scail2-output.mp4","file_size":1048576,"content_type":"video/mp4"}

- **`seed`** (`integer`, _required_):
  The seed used to generate the video.

- **`preprocessing_video`** (`File`, _optional_):
  Debug (only when `output_preprocessing=true`): the Stage-A pose-conditioning video fed to the diffusion model — the rendered NLF/DWPose skeleton for `driving_type=pose`, or the SAM3-masked driving video for `end_to_end`.

- **`preprocessing_mask_video`** (`File`, _optional_):
  Debug (only when `output_preprocessing=true`): the Stage-A driving mask video.



**Example Response**:

```json
{
  "video": {
    "file_name": "output.mp4",
    "url": "https://storage.googleapis.com/falserverless/example_outputs/scail2-output.mp4",
    "file_size": 1048576,
    "content_type": "video/mp4"
  }
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/scail-2 \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "A person dancing gracefully in a sunlit studio",
     "image_url": "https://v3b.fal.media/files/b/panda/-oMlZo9Yyj_Nzoza_tgds_GmLF86r5bOt50eMMKCszy_eacc949b3933443c9915a83c98fbe85e.png",
     "video_url": "https://v3b.fal.media/files/b/panda/a6SvJg96V8eoglMlYFShU_5385885-hd_1080_1920_25fps.mp4"
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
    "fal-ai/scail-2",
    arguments={
        "prompt": "A person dancing gracefully in a sunlit studio",
        "image_url": "https://v3b.fal.media/files/b/panda/-oMlZo9Yyj_Nzoza_tgds_GmLF86r5bOt50eMMKCszy_eacc949b3933443c9915a83c98fbe85e.png",
        "video_url": "https://v3b.fal.media/files/b/panda/a6SvJg96V8eoglMlYFShU_5385885-hd_1080_1920_25fps.mp4"
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

const result = await fal.subscribe("fal-ai/scail-2", {
  input: {
    prompt: "A person dancing gracefully in a sunlit studio",
    image_url: "https://v3b.fal.media/files/b/panda/-oMlZo9Yyj_Nzoza_tgds_GmLF86r5bOt50eMMKCszy_eacc949b3933443c9915a83c98fbe85e.png",
    video_url: "https://v3b.fal.media/files/b/panda/a6SvJg96V8eoglMlYFShU_5385885-hd_1080_1920_25fps.mp4"
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

- [Model Playground](https://fal.ai/models/fal-ai/scail-2)
- [API Documentation](https://fal.ai/models/fal-ai/scail-2/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/scail-2)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
