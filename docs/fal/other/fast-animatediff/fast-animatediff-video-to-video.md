# AnimateDiff

> Re-animate your videos!


## Overview

- **Endpoint**: `https://fal.run/fal-ai/fast-animatediff/video-to-video`
- **Model ID**: `fal-ai/fast-animatediff/video-to-video`
- **Category**: video-to-video
- **Kind**: inference
**Tags**: animation, stylized



## Pricing

- **Price**: $0 per compute seconds

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`video_url`** (`string`, _required_):
  URL of the video.
  - Examples: "https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/diffusers/animatediff-vid2vid-input-2.gif", "https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/diffusers/animatediff-vid2vid-input-1.gif"

- **`first_n_seconds`** (`integer`, _optional_):
  The first N number of seconds of video to animate. Default value: `3`
  - Default: `3`
  - Range: `2` to `4`

- **`prompt`** (`string`, _required_):
  The prompt to use for generating the image. Be as descriptive as possible for best results.
  - Examples: "closeup of tony stark, robert downey jr, fireworks, high quality, ultra HD", "panda playing a guitar, on a boat, in the ocean, high quality, high quality, ultra HD, realistic"

- **`negative_prompt`** (`string`, _optional_):
  The negative prompt to use. Use it to address details that you don't want
  in the image. This could be colors, objects, scenery and even the small details
  (e.g. moustache, blurry, low resolution). Default value: `"(bad quality, worst quality:1.2), ugly faces, bad anime"`
  - Default: `"(bad quality, worst quality:1.2), ugly faces, bad anime"`

- **`num_inference_steps`** (`integer`, _optional_):
  The number of inference steps to perform. Default value: `25`
  - Default: `25`
  - Range: `1` to `50`

- **`strength`** (`float`, _optional_):
  The strength of the input video in the final output. Default value: `0.7`
  - Default: `0.7`
  - Range: `0` to `1`

- **`guidance_scale`** (`float`, _optional_):
  The CFG (Classifier Free Guidance) scale is a measure of how close you want
  the model to stick to your prompt when looking for a related image to show you. Default value: `7.5`
  - Default: `7.5`
  - Range: `0` to `20`

- **`seed`** (`integer`, _optional_):
  The same seed and the same prompt given to the same version of Stable Diffusion
  will output the same image every time.

- **`fps`** (`integer`, _optional_):
  Number of frames per second to extract from the video. Default value: `8`
  - Default: `8`
  - Range: `1` to `16`

- **`motions`** (`list<Enum>`, _optional_):
  The motions to apply to the video.
  - Array of Enum



**Required Parameters Example**:

```json
{
  "video_url": "https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/diffusers/animatediff-vid2vid-input-2.gif",
  "prompt": "closeup of tony stark, robert downey jr, fireworks, high quality, ultra HD"
}
```

**Full Example**:

```json
{
  "video_url": "https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/diffusers/animatediff-vid2vid-input-2.gif",
  "first_n_seconds": 3,
  "prompt": "closeup of tony stark, robert downey jr, fireworks, high quality, ultra HD",
  "negative_prompt": "(bad quality, worst quality:1.2), ugly faces, bad anime",
  "num_inference_steps": 25,
  "strength": 0.7,
  "guidance_scale": 7.5,
  "fps": 8
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`File`, _required_):
  Generated video file.
  - Examples: {"url":"https://fal-cdn.batuhan-941.workers.dev/files/koala/5Cb_6P_s9wW8f8-g9c4yj.mp4"}

- **`seed`** (`integer`, _required_):
  Seed used for generating the video.



**Example Response**:

```json
{
  "video": {
    "url": "https://fal-cdn.batuhan-941.workers.dev/files/koala/5Cb_6P_s9wW8f8-g9c4yj.mp4"
  }
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/fast-animatediff/video-to-video \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "video_url": "https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/diffusers/animatediff-vid2vid-input-2.gif",
     "prompt": "closeup of tony stark, robert downey jr, fireworks, high quality, ultra HD"
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
    "fal-ai/fast-animatediff/video-to-video",
    arguments={
        "video_url": "https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/diffusers/animatediff-vid2vid-input-2.gif",
        "prompt": "closeup of tony stark, robert downey jr, fireworks, high quality, ultra HD"
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

const result = await fal.subscribe("fal-ai/fast-animatediff/video-to-video", {
  input: {
    video_url: "https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/diffusers/animatediff-vid2vid-input-2.gif",
    prompt: "closeup of tony stark, robert downey jr, fireworks, high quality, ultra HD"
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

- [Model Playground](https://fal.ai/models/fal-ai/fast-animatediff/video-to-video)
- [API Documentation](https://fal.ai/models/fal-ai/fast-animatediff/video-to-video/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/fast-animatediff/video-to-video)
- [GitHub Repository](https://github.com/guoyww/AnimateDiff/blob/main/LICENSE.txt)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
