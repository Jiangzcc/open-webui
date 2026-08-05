# Wan Motion

> Wan Motion is a streamlined character animation model that transfers motion from a driving video onto a reference character image. Based on Wan-Animate which preserves the original character's proportions, Simple uses pose retargeting to adapt the driving video's skeleton to match the reference character's body shape, producing more natural results when the two have different builds. It outputs at 720p with optimized defaults for fast, high-quality generation — just provide a video, an image, and an optional prompt.


## Overview

- **Endpoint**: `https://fal.run/fal-ai/wan-motion`
- **Model ID**: `fal-ai/wan-motion`
- **Category**: video-to-video
- **Kind**: inference


## Pricing

Your request will cost $0.06 per video second for 720p. Video seconds are calculated at 24 frames per second. When enhance_identity is enabled, an additional $0.08 is charged for Flux 2 Edit image preprocessing. 

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`video_url`** (`string`, _required_):
  URL of the driving video (provides the motion).
  - Examples: "https://v3b.fal.media/files/b/0a8f0997/JuDW2xl0mr6sJ_Kjz3Vxe_vidoeook.mp4"

- **`image_url`** (`string`, _required_):
  URL of the reference image (provides the character appearance).
  - Examples: "https://v3b.fal.media/files/b/0a8f0995/slF9l2eNL_YSD7SqU7tUz_i35fsR92.jpg"

- **`prompt`** (`string`, _optional_):
  Optional text prompt to guide the generation. Default value: `""`
  - Default: `""`
  - Examples: "woman dancing"

- **`seed`** (`integer`, _optional_):
  Random seed for reproducibility.

- **`acceleration`** (`AccelerationEnum`, _optional_):
  Acceleration level to use. 'regular' enables caching for faster generation, 'none' disables it. Default value: `"regular"`
  - Default: `"regular"`
  - Options: `"none"`, `"regular"`

- **`adapt_motion`** (`boolean`, _optional_):
  Adapts the driving video's motion to match the reference image's body proportions. Recommended when the driving video subject and reference image have different body shapes or sizes. Default value: `true`
  - Default: `true`

- **`enhance_identity`** (`boolean`, _optional_):
  Enhances identity preservation by preprocessing the reference image with Flux Kontext Edit before animation. Produces more faithful face and appearance transfer at the cost of slightly longer processing time.
  - Default: `false`

- **`enable_safety_checker`** (`boolean`, _optional_):
  If set to true, input and output will be checked for safety. Default value: `true`
  - Default: `true`



**Required Parameters Example**:

```json
{
  "video_url": "https://v3b.fal.media/files/b/0a8f0997/JuDW2xl0mr6sJ_Kjz3Vxe_vidoeook.mp4",
  "image_url": "https://v3b.fal.media/files/b/0a8f0995/slF9l2eNL_YSD7SqU7tUz_i35fsR92.jpg"
}
```

**Full Example**:

```json
{
  "video_url": "https://v3b.fal.media/files/b/0a8f0997/JuDW2xl0mr6sJ_Kjz3Vxe_vidoeook.mp4",
  "image_url": "https://v3b.fal.media/files/b/0a8f0995/slF9l2eNL_YSD7SqU7tUz_i35fsR92.jpg",
  "prompt": "woman dancing",
  "acceleration": "regular",
  "adapt_motion": true,
  "enable_safety_checker": true
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`File`, _required_):
  The generated video file.
  - Examples: {"url":"https://v3b.fal.media/files/b/0a8f2447/EjMyhbOyYfxL8tDM9T59K_wan_animate_output.mp4"}

- **`prompt`** (`string`, _optional_):
  The prompt used for generation. Default value: `""`
  - Default: `""`
  - Examples: "woman dancing"

- **`seed`** (`integer`, _required_):
  The seed used for generation.
  - Examples: 924575000



**Example Response**:

```json
{
  "video": {
    "url": "https://v3b.fal.media/files/b/0a8f2447/EjMyhbOyYfxL8tDM9T59K_wan_animate_output.mp4"
  },
  "prompt": "woman dancing",
  "seed": 924575000
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/wan-motion \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "video_url": "https://v3b.fal.media/files/b/0a8f0997/JuDW2xl0mr6sJ_Kjz3Vxe_vidoeook.mp4",
     "image_url": "https://v3b.fal.media/files/b/0a8f0995/slF9l2eNL_YSD7SqU7tUz_i35fsR92.jpg"
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
    "fal-ai/wan-motion",
    arguments={
        "video_url": "https://v3b.fal.media/files/b/0a8f0997/JuDW2xl0mr6sJ_Kjz3Vxe_vidoeook.mp4",
        "image_url": "https://v3b.fal.media/files/b/0a8f0995/slF9l2eNL_YSD7SqU7tUz_i35fsR92.jpg"
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

const result = await fal.subscribe("fal-ai/wan-motion", {
  input: {
    video_url: "https://v3b.fal.media/files/b/0a8f0997/JuDW2xl0mr6sJ_Kjz3Vxe_vidoeook.mp4",
    image_url: "https://v3b.fal.media/files/b/0a8f0995/slF9l2eNL_YSD7SqU7tUz_i35fsR92.jpg"
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

- [Model Playground](https://fal.ai/models/fal-ai/wan-motion)
- [API Documentation](https://fal.ai/models/fal-ai/wan-motion/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/wan-motion)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
