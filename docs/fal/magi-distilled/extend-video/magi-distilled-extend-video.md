# MAGI-1 (Distilled)

> MAGI-1 distilled extends videos faster with an exceptional understanding of physical interactions and prompts


## Overview

- **Endpoint**: `https://fal.run/fal-ai/magi-distilled/extend-video`
- **Model ID**: `fal-ai/magi-distilled/extend-video`
- **Category**: video-to-video
- **Kind**: inference
**Tags**: video-to-video, video-extend



## Pricing

Your request will cost $0.32 to generate one four-second video. For $1 you can run this model approximately 3 times. 

Additional seconds will cost $0.08 each, calculated at 24 frames per second.

Additional inference steps above 16 incur a 1/16 multiplier each, such that your total cost will be multiplied x2 at 32 steps.

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _required_):
  The text prompt to guide video generation.
  - Examples: ""

- **`video_url`** (`string`, _required_):
  URL of the input video to represent the beginning of the video. If the input video does not match the chosen aspect ratio, it is resized and center cropped.
  - Examples: "https://v3.fal.media/files/rabbit/lTH9PY_LQG0FjueBxMfDN_0395dec3-0c4a-4c25-8399-ebb198b73a30.mp4"

- **`num_frames`** (`integer`, _optional_):
  Number of frames to generate. Must be between 96 and 192 (inclusive). Each additional 24 frames beyond 96 incurs an additional billing unit. Default value: `96`
  - Default: `96`
  - Range: `96` to `192`

- **`start_frame`** (`integer`, _optional_):
  The frame to begin the generation from, with the remaining frames will be treated as the prefix video. The final video will contain the frames up until this number unchanged, followed by the generated frames. The default start frame is 32 frames before the end of the video, which gives optimal results.

- **`seed`** (`integer`, _optional_):
  Random seed for reproducibility. If None, a random seed is chosen.

- **`resolution`** (`ResolutionEnum`, _optional_):
  Resolution of the generated video (480p or 720p). 480p is 0.5 billing units, and 720p is 1 billing unit. Default value: `"720p"`
  - Default: `"720p"`
  - Options: `"480p"`, `"720p"`

- **`num_inference_steps`** (`NumInferenceStepsEnum`, _optional_):
  Number of inference steps for sampling. Higher values give better quality but take longer. Default value: `"16"`
  - Default: `16`
  - Options: `4`, `8`, `16`, `32`

- **`enable_safety_checker`** (`boolean`, _optional_):
  If set to true, the safety checker will be enabled. Default value: `true`
  - Default: `true`
  - Examples: true

- **`aspect_ratio`** (`AspectRatioEnum`, _optional_):
  Aspect ratio of the generated video. If 'auto', the aspect ratio will be determined automatically based on the input image. Default value: `"auto"`
  - Default: `"auto"`
  - Options: `"auto"`, `"16:9"`, `"9:16"`, `"1:1"`



**Required Parameters Example**:

```json
{
  "prompt": "",
  "video_url": "https://v3.fal.media/files/rabbit/lTH9PY_LQG0FjueBxMfDN_0395dec3-0c4a-4c25-8399-ebb198b73a30.mp4"
}
```

**Full Example**:

```json
{
  "prompt": "",
  "video_url": "https://v3.fal.media/files/rabbit/lTH9PY_LQG0FjueBxMfDN_0395dec3-0c4a-4c25-8399-ebb198b73a30.mp4",
  "num_frames": 96,
  "resolution": "720p",
  "num_inference_steps": 16,
  "enable_safety_checker": true,
  "aspect_ratio": "auto"
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`File`, _required_):
  The generated video file.
  - Examples: {"url":"https://v3.fal.media/files/zebra/2UjT7u_8oF2gGfxBiT_gL_91a8f175-fd57-4ed6-aedc-1957aa558363.mp4"}

- **`seed`** (`integer`, _required_):
  The seed used for generation.



**Example Response**:

```json
{
  "video": {
    "url": "https://v3.fal.media/files/zebra/2UjT7u_8oF2gGfxBiT_gL_91a8f175-fd57-4ed6-aedc-1957aa558363.mp4"
  }
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/magi-distilled/extend-video \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "",
     "video_url": "https://v3.fal.media/files/rabbit/lTH9PY_LQG0FjueBxMfDN_0395dec3-0c4a-4c25-8399-ebb198b73a30.mp4"
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
    "fal-ai/magi-distilled/extend-video",
    arguments={
        "prompt": "",
        "video_url": "https://v3.fal.media/files/rabbit/lTH9PY_LQG0FjueBxMfDN_0395dec3-0c4a-4c25-8399-ebb198b73a30.mp4"
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

const result = await fal.subscribe("fal-ai/magi-distilled/extend-video", {
  input: {
    prompt: "",
    video_url: "https://v3.fal.media/files/rabbit/lTH9PY_LQG0FjueBxMfDN_0395dec3-0c4a-4c25-8399-ebb198b73a30.mp4"
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

- [Model Playground](https://fal.ai/models/fal-ai/magi-distilled/extend-video)
- [API Documentation](https://fal.ai/models/fal-ai/magi-distilled/extend-video/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/magi-distilled/extend-video)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
