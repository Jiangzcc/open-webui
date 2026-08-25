# LTX-Video 13B 0.9.8 Distilled

> Extend videos using LTX Video-0.9.8 13B Distilled and custom LoRA


## Overview

- **Endpoint**: `https://fal.run/fal-ai/ltxv-13b-098-distilled/extend`
- **Model ID**: `fal-ai/ltxv-13b-098-distilled/extend`
- **Category**: video-to-video
- **Kind**: inference
**Tags**: ltx-video, extend



## Pricing

Your request will cost **$0.02** per second, billed at 24 frames per second. For $1 you can generate **50 seconds** of video. Enabling `detail_pass` will **double** the billed seconds.

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _required_):
  Text prompt to guide generation
  - Examples: "Woman walking on a street in Tokyo"

- **`negative_prompt`** (`string`, _optional_):
  Negative prompt for generation Default value: `"worst quality, inconsistent motion, blurry, jittery, distorted"`
  - Default: `"worst quality, inconsistent motion, blurry, jittery, distorted"`

- **`loras`** (`list<LoRAWeight>`, _optional_):
  LoRA weights to use for generation
  - Default: `[]`
  - Array of LoRAWeight

- **`resolution`** (`ResolutionEnum`, _optional_):
  Resolution of the generated video. Default value: `"720p"`
  - Default: `"720p"`
  - Options: `"480p"`, `"720p"`
  - Examples: "720p"

- **`aspect_ratio`** (`AspectRatioEnum`, _optional_):
  The aspect ratio of the video. Default value: `"auto"`
  - Default: `"auto"`
  - Options: `"9:16"`, `"1:1"`, `"16:9"`, `"auto"`
  - Examples: "auto"

- **`seed`** (`integer`, _optional_):
  Random seed for generation

- **`num_frames`** (`integer`, _optional_):
  The number of frames in the video. Default value: `121`
  - Default: `121`
  - Range: `9` to `1441`
  - Examples: 121

- **`first_pass_num_inference_steps`** (`integer`, _optional_):
  Number of inference steps during the first pass. Default value: `8`
  - Default: `8`
  - Range: `2` to `12`
  - Examples: 8

- **`second_pass_num_inference_steps`** (`integer`, _optional_):
  Number of inference steps during the second pass. Default value: `8`
  - Default: `8`
  - Range: `2` to `12`
  - Examples: 8

- **`second_pass_skip_initial_steps`** (`integer`, _optional_):
  The number of inference steps to skip in the initial steps of the second pass. By skipping some steps at the beginning, the second pass can focus on smaller details instead of larger changes. Default value: `5`
  - Default: `5`
  - Range: `1` to `11`
  - Examples: 5

- **`frame_rate`** (`integer`, _optional_):
  The frame rate of the video. Default value: `24`
  - Default: `24`
  - Range: `1` to `60`
  - Examples: 24

- **`expand_prompt`** (`boolean`, _optional_):
  Whether to expand the prompt using a language model.
  - Default: `false`
  - Examples: false

- **`reverse_video`** (`boolean`, _optional_):
  Whether to reverse the video.
  - Default: `false`
  - Examples: false

- **`enable_safety_checker`** (`boolean`, _optional_):
  Whether to enable the safety checker. Default value: `true`
  - Default: `true`
  - Examples: true

- **`enable_detail_pass`** (`boolean`, _optional_):
  Whether to use a detail pass. If True, the model will perform a second pass to refine the video and enhance details. This incurs a 2.0x cost multiplier on the base price.
  - Default: `false`
  - Examples: false

- **`temporal_adain_factor`** (`float`, _optional_):
  The factor for adaptive instance normalization (AdaIN) applied to generated video chunks after the first. This can help deal with a gradual increase in saturation/contrast in the generated video by normalizing the color distribution across the video. A high value will ensure the color distribution is more consistent across the video, while a low value will allow for more variation in color distribution. Default value: `0.5`
  - Default: `0.5`
  - Range: `0` to `1`, step: `0.05`
  - Examples: 0.5

- **`tone_map_compression_ratio`** (`float`, _optional_):
  The compression ratio for tone mapping. This is used to compress the dynamic range of the video to improve visual quality. A value of 0.0 means no compression, while a value of 1.0 means maximum compression.
  - Default: `0`
  - Range: `0` to `1`, step: `0.05`
  - Examples: 0

- **`constant_rate_factor`** (`integer`, _optional_):
  The constant rate factor (CRF) to compress input media with. Compressed input media more closely matches the model's training data, which can improve motion quality. Default value: `29`
  - Default: `29`
  - Range: `0` to `51`
  - Examples: 29

- **`video`** (`ExtendVideoConditioningInput`, _required_):
  Video to be extended.
  - Examples: {"limit_num_frames":false,"preprocess":false,"resample_fps":false,"conditioning_type":"rgb","reverse_video":false,"video_url":"https://storage.googleapis.com/falserverless/web-examples/wan/t2v.mp4","target_fps":24,"max_num_frames":1441,"start_frame_num":0,"strength":1}



**Required Parameters Example**:

```json
{
  "prompt": "Woman walking on a street in Tokyo",
  "video": {
    "limit_num_frames": false,
    "preprocess": false,
    "resample_fps": false,
    "conditioning_type": "rgb",
    "reverse_video": false,
    "video_url": "https://storage.googleapis.com/falserverless/web-examples/wan/t2v.mp4",
    "target_fps": 24,
    "max_num_frames": 1441,
    "start_frame_num": 0,
    "strength": 1
  }
}
```

**Full Example**:

```json
{
  "prompt": "Woman walking on a street in Tokyo",
  "negative_prompt": "worst quality, inconsistent motion, blurry, jittery, distorted",
  "loras": [],
  "resolution": "720p",
  "aspect_ratio": "auto",
  "num_frames": 121,
  "first_pass_num_inference_steps": 8,
  "second_pass_num_inference_steps": 8,
  "second_pass_skip_initial_steps": 5,
  "frame_rate": 24,
  "expand_prompt": false,
  "reverse_video": false,
  "enable_safety_checker": true,
  "enable_detail_pass": false,
  "temporal_adain_factor": 0.5,
  "tone_map_compression_ratio": 0,
  "constant_rate_factor": 29,
  "video": {
    "limit_num_frames": false,
    "preprocess": false,
    "resample_fps": false,
    "conditioning_type": "rgb",
    "reverse_video": false,
    "video_url": "https://storage.googleapis.com/falserverless/web-examples/wan/t2v.mp4",
    "target_fps": 24,
    "max_num_frames": 1441,
    "start_frame_num": 0,
    "strength": 1
  }
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`File`, _required_):
  The generated video file.
  - Examples: {"url":"https://storage.googleapis.com/falserverless/example_outputs/ltx-v095_extend.mp4"}

- **`prompt`** (`string`, _required_):
  The prompt used for generation.
  - Examples: "Woman walking on a street in Tokyo"

- **`seed`** (`integer`, _required_):
  The seed used for generation.



**Example Response**:

```json
{
  "video": {
    "url": "https://storage.googleapis.com/falserverless/example_outputs/ltx-v095_extend.mp4"
  },
  "prompt": "Woman walking on a street in Tokyo"
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/ltxv-13b-098-distilled/extend \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "Woman walking on a street in Tokyo",
     "video": {
       "limit_num_frames": false,
       "preprocess": false,
       "resample_fps": false,
       "conditioning_type": "rgb",
       "reverse_video": false,
       "video_url": "https://storage.googleapis.com/falserverless/web-examples/wan/t2v.mp4",
       "target_fps": 24,
       "max_num_frames": 1441,
       "start_frame_num": 0,
       "strength": 1
     }
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
    "fal-ai/ltxv-13b-098-distilled/extend",
    arguments={
        "prompt": "Woman walking on a street in Tokyo",
        "video": {
            "limit_num_frames": False,
            "preprocess": False,
            "resample_fps": False,
            "conditioning_type": "rgb",
            "reverse_video": False,
            "video_url": "https://storage.googleapis.com/falserverless/web-examples/wan/t2v.mp4",
            "target_fps": 24,
            "max_num_frames": 1441,
            "start_frame_num": 0,
            "strength": 1
        }
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

const result = await fal.subscribe("fal-ai/ltxv-13b-098-distilled/extend", {
  input: {
    prompt: "Woman walking on a street in Tokyo",
    video: {
      limit_num_frames: false,
      preprocess: false,
      resample_fps: false,
      conditioning_type: "rgb",
      reverse_video: false,
      video_url: "https://storage.googleapis.com/falserverless/web-examples/wan/t2v.mp4",
      target_fps: 24,
      max_num_frames: 1441,
      start_frame_num: 0,
      strength: 1
    }
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

- [Model Playground](https://fal.ai/models/fal-ai/ltxv-13b-098-distilled/extend)
- [API Documentation](https://fal.ai/models/fal-ai/ltxv-13b-098-distilled/extend/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/ltxv-13b-098-distilled/extend)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
