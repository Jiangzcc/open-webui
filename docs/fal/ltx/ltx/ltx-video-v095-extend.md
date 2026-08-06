# LTX Video-0.9.5

> Generate videos from prompts and videos using LTX Video-0.9.5


## Overview

- **Endpoint**: `https://fal.run/fal-ai/ltx-video-v095/extend`
- **Model ID**: `fal-ai/ltx-video-v095/extend`
- **Category**: video-to-video
- **Kind**: inference
**Tags**: video, video-to-video



## Pricing

- **Price**: $0.04 per videos

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

- **`resolution`** (`ResolutionEnum`, _optional_):
  Resolution of the generated video (480p or 720p). Default value: `"720p"`
  - Default: `"720p"`
  - Options: `"480p"`, `"720p"`

- **`aspect_ratio`** (`AspectRatioEnum`, _optional_):
  Aspect ratio of the generated video (16:9 or 9:16). Default value: `"16:9"`
  - Default: `"16:9"`
  - Options: `"9:16"`, `"16:9"`

- **`seed`** (`integer`, _optional_):
  Random seed for generation

- **`num_inference_steps`** (`integer`, _optional_):
  Number of inference steps Default value: `40`
  - Default: `40`
  - Range: `2` to `50`

- **`expand_prompt`** (`boolean`, _optional_):
  Whether to expand the prompt using the model's own capabilities. Default value: `true`
  - Default: `true`

- **`video`** (`VideoConditioningInput`, _required_):
  Video to be extended.
  - Examples: {"start_frame_num":24,"video_url":"https://storage.googleapis.com/falserverless/web-examples/wan/t2v.mp4"}



**Required Parameters Example**:

```json
{
  "prompt": "Woman walking on a street in Tokyo",
  "video": {
    "start_frame_num": 24,
    "video_url": "https://storage.googleapis.com/falserverless/web-examples/wan/t2v.mp4"
  }
}
```

**Full Example**:

```json
{
  "prompt": "Woman walking on a street in Tokyo",
  "negative_prompt": "worst quality, inconsistent motion, blurry, jittery, distorted",
  "resolution": "720p",
  "aspect_ratio": "16:9",
  "num_inference_steps": 40,
  "expand_prompt": true,
  "video": {
    "start_frame_num": 24,
    "video_url": "https://storage.googleapis.com/falserverless/web-examples/wan/t2v.mp4"
  }
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`File`, _required_):
  The generated video file.
  - Examples: {"url":"https://storage.googleapis.com/falserverless/example_outputs/ltx-v095_extend.mp4"}

- **`seed`** (`integer`, _required_):
  The seed used for generation.



**Example Response**:

```json
{
  "video": {
    "url": "https://storage.googleapis.com/falserverless/example_outputs/ltx-v095_extend.mp4"
  }
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/ltx-video-v095/extend \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "Woman walking on a street in Tokyo",
     "video": {
       "start_frame_num": 24,
       "video_url": "https://storage.googleapis.com/falserverless/web-examples/wan/t2v.mp4"
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
    "fal-ai/ltx-video-v095/extend",
    arguments={
        "prompt": "Woman walking on a street in Tokyo",
        "video": {
            "start_frame_num": 24,
            "video_url": "https://storage.googleapis.com/falserverless/web-examples/wan/t2v.mp4"
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

const result = await fal.subscribe("fal-ai/ltx-video-v095/extend", {
  input: {
    prompt: "Woman walking on a street in Tokyo",
    video: {
      start_frame_num: 24,
      video_url: "https://storage.googleapis.com/falserverless/web-examples/wan/t2v.mp4"
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

- [Model Playground](https://fal.ai/models/fal-ai/ltx-video-v095/extend)
- [API Documentation](https://fal.ai/models/fal-ai/ltx-video-v095/extend/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/ltx-video-v095/extend)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
