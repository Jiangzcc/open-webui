# PixVerse V3.5 Transition

> Create seamless transition between images using PixVerse v3.5


## Overview

- **Endpoint**: `https://fal.run/fal-ai/pixverse/v3.5/transition`
- **Model ID**: `fal-ai/pixverse/v3.5/transition`
- **Category**: image-to-video
- **Kind**: inference


## Pricing

For 5s video your request will cost **$0.15** for 360p and 540p, **$0.2** for 720p and **$0.4** for 1080p. For **$1** you can run this model with approximately 2 times.

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _required_):
  The prompt for the transition. Limited to 2048 UTF-8 encoded bytes. Because the limit counts bytes rather than characters, emoji and non-Latin or accented characters (which use multiple bytes each) can push a visually short prompt over the cap.
  - Examples: "Scene slowly transition into cat swimming under water"

- **`aspect_ratio`** (`AspectRatioEnum`, _optional_):
  The aspect ratio of the generated video Default value: `"16:9"`
  - Default: `"16:9"`
  - Options: `"16:9"`, `"4:3"`, `"1:1"`, `"3:4"`, `"9:16"`

- **`resolution`** (`ResolutionEnum`, _optional_):
  The resolution of the generated video Default value: `"720p"`
  - Default: `"720p"`
  - Options: `"360p"`, `"540p"`, `"720p"`, `"1080p"`

- **`duration`** (`DurationEnum`, _optional_):
  The duration of the generated video in seconds Default value: `"5"`
  - Default: `"5"`
  - Options: `"5"`, `"8"`

- **`negative_prompt`** (`string`, _optional_):
  Negative prompt to be used for the generation. Limited to 2048 UTF-8 encoded bytes. Because the limit counts bytes rather than characters, emoji and non-Latin or accented characters (which use multiple bytes each) can push a visually short prompt over the cap. Default value: `""`
  - Default: `""`
  - Examples: "blurry, low quality, low resolution, pixelated, noisy, grainy, out of focus, poorly lit, poorly exposed, poorly composed, poorly framed, poorly cropped, poorly color corrected, poorly color graded"

- **`style`** (`Enum`, _optional_):
  The style of the generated video
  - Options: `"anime"`, `"3d_animation"`, `"clay"`, `"comic"`, `"cyberpunk"`

- **`seed`** (`integer`, _optional_):
  The same seed and the same prompt given to the same version of the model
  will output the same video every time.

- **`first_image_url`** (`string`, _required_):
  URL of the image to use as the first frame
  - Examples: "https://v3.fal.media/files/zebra/owQh2DAzk8UU7J02nr5RY_Co2P4boLv6meIZ5t9gKvL_8685da151df343ab8bf82165c928e2a5.jpg"

- **`end_image_url`** (`string`, _required_):
  URL of the image to use as the last frame
  - Examples: "https://v3.fal.media/files/kangaroo/RgedFs_WSnq5BgER7qDx1_ONrbTJ1YAGXz-9JnSsBoB_bdc8750387734bfe940319f469f7b0b2.jpg"



**Required Parameters Example**:

```json
{
  "prompt": "Scene slowly transition into cat swimming under water",
  "first_image_url": "https://v3.fal.media/files/zebra/owQh2DAzk8UU7J02nr5RY_Co2P4boLv6meIZ5t9gKvL_8685da151df343ab8bf82165c928e2a5.jpg",
  "end_image_url": "https://v3.fal.media/files/kangaroo/RgedFs_WSnq5BgER7qDx1_ONrbTJ1YAGXz-9JnSsBoB_bdc8750387734bfe940319f469f7b0b2.jpg"
}
```

**Full Example**:

```json
{
  "prompt": "Scene slowly transition into cat swimming under water",
  "aspect_ratio": "16:9",
  "resolution": "720p",
  "duration": "5",
  "negative_prompt": "blurry, low quality, low resolution, pixelated, noisy, grainy, out of focus, poorly lit, poorly exposed, poorly composed, poorly framed, poorly cropped, poorly color corrected, poorly color graded",
  "first_image_url": "https://v3.fal.media/files/zebra/owQh2DAzk8UU7J02nr5RY_Co2P4boLv6meIZ5t9gKvL_8685da151df343ab8bf82165c928e2a5.jpg",
  "end_image_url": "https://v3.fal.media/files/kangaroo/RgedFs_WSnq5BgER7qDx1_ONrbTJ1YAGXz-9JnSsBoB_bdc8750387734bfe940319f469f7b0b2.jpg"
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`File`, _required_):
  The generated video
  - Examples: {"file_size":3890360,"file_name":"output.mp4","content_type":"video/mp4","url":"https://fal.media/files/panda/5KmKS-mh1vO-htbqE5oex_output.mp4"}



**Example Response**:

```json
{
  "video": {
    "file_size": 3890360,
    "file_name": "output.mp4",
    "content_type": "video/mp4",
    "url": "https://fal.media/files/panda/5KmKS-mh1vO-htbqE5oex_output.mp4"
  }
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/pixverse/v3.5/transition \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "Scene slowly transition into cat swimming under water",
     "first_image_url": "https://v3.fal.media/files/zebra/owQh2DAzk8UU7J02nr5RY_Co2P4boLv6meIZ5t9gKvL_8685da151df343ab8bf82165c928e2a5.jpg",
     "end_image_url": "https://v3.fal.media/files/kangaroo/RgedFs_WSnq5BgER7qDx1_ONrbTJ1YAGXz-9JnSsBoB_bdc8750387734bfe940319f469f7b0b2.jpg"
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
    "fal-ai/pixverse/v3.5/transition",
    arguments={
        "prompt": "Scene slowly transition into cat swimming under water",
        "first_image_url": "https://v3.fal.media/files/zebra/owQh2DAzk8UU7J02nr5RY_Co2P4boLv6meIZ5t9gKvL_8685da151df343ab8bf82165c928e2a5.jpg",
        "end_image_url": "https://v3.fal.media/files/kangaroo/RgedFs_WSnq5BgER7qDx1_ONrbTJ1YAGXz-9JnSsBoB_bdc8750387734bfe940319f469f7b0b2.jpg"
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

const result = await fal.subscribe("fal-ai/pixverse/v3.5/transition", {
  input: {
    prompt: "Scene slowly transition into cat swimming under water",
    first_image_url: "https://v3.fal.media/files/zebra/owQh2DAzk8UU7J02nr5RY_Co2P4boLv6meIZ5t9gKvL_8685da151df343ab8bf82165c928e2a5.jpg",
    end_image_url: "https://v3.fal.media/files/kangaroo/RgedFs_WSnq5BgER7qDx1_ONrbTJ1YAGXz-9JnSsBoB_bdc8750387734bfe940319f469f7b0b2.jpg"
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

- [Model Playground](https://fal.ai/models/fal-ai/pixverse/v3.5/transition)
- [API Documentation](https://fal.ai/models/fal-ai/pixverse/v3.5/transition/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/pixverse/v3.5/transition)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
