# Framepack F1

> Framepack is an efficient Image-to-video model that autoregressively generates videos.


## Overview

- **Endpoint**: `https://fal.run/fal-ai/framepack/f1`
- **Model ID**: `fal-ai/framepack/f1`
- **Category**: image-to-video
- **Kind**: inference
**Tags**: image to video, motion



## Pricing

- **Price**: $0.0333 per seconds

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _required_):
  Text prompt for video generation (max 500 characters).
  - Examples: "A mesmerising video of a deep sea jellyfish moving through an inky-black ocean. The jellyfish glows softly with an amber bioluminescence. The overall scene is lifelike."

- **`negative_prompt`** (`string`, _optional_):
  Negative prompt for video generation. Default value: `""`
  - Default: `""`
  - Examples: "Ugly, blurry distorted, bad quality"

- **`image_url`** (`string`, _required_):
  URL of the image input.
  - Examples: "https://storage.googleapis.com/falserverless/framepack/framepack.jpg"

- **`seed`** (`integer`, _optional_):
  The seed to use for generating the video.

- **`aspect_ratio`** (`AspectRatio(W:H)Enum`, _optional_):
  The aspect ratio of the video to generate. Default value: `"16:9"`
  - Default: `"16:9"`
  - Options: `"16:9"`, `"9:16"`

- **`resolution`** (`ResolutionEnum`, _optional_):
  The resolution of the video to generate. 720p generations cost 1.5x more than 480p generations. Default value: `"480p"`
  - Default: `"480p"`
  - Options: `"720p"`, `"480p"`

- **`cfg_scale`** (`float`, _optional_):
  Classifier-Free Guidance scale for the generation. Default value: `1`
  - Default: `1`
  - Range: `0` to `7`

- **`guidance_scale`** (`float`, _optional_):
  Guidance scale for the generation. Default value: `10`
  - Default: `10`
  - Range: `0` to `32`

- **`num_frames`** (`integer`, _optional_):
  The number of frames to generate. Default value: `180`
  - Default: `180`
  - Range: `30` to `900`

- **`enable_safety_checker`** (`boolean`, _optional_):
  If set to true, the safety checker will be enabled.
  - Default: `false`
  - Examples: true



**Required Parameters Example**:

```json
{
  "prompt": "A mesmerising video of a deep sea jellyfish moving through an inky-black ocean. The jellyfish glows softly with an amber bioluminescence. The overall scene is lifelike.",
  "image_url": "https://storage.googleapis.com/falserverless/framepack/framepack.jpg"
}
```

**Full Example**:

```json
{
  "prompt": "A mesmerising video of a deep sea jellyfish moving through an inky-black ocean. The jellyfish glows softly with an amber bioluminescence. The overall scene is lifelike.",
  "negative_prompt": "Ugly, blurry distorted, bad quality",
  "image_url": "https://storage.googleapis.com/falserverless/framepack/framepack.jpg",
  "aspect_ratio": "16:9",
  "resolution": "480p",
  "cfg_scale": 1,
  "guidance_scale": 10,
  "num_frames": 180,
  "enable_safety_checker": true
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`File`, _required_)
  - Examples: {"url":"https://storage.googleapis.com/falserverless/framepack/TfJPbwm6_D60dcWEv9LVX_output_video.mp4"}

- **`seed`** (`integer`, _required_):
  The seed used for generating the video.



**Example Response**:

```json
{
  "video": {
    "url": "https://storage.googleapis.com/falserverless/framepack/TfJPbwm6_D60dcWEv9LVX_output_video.mp4"
  }
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/framepack/f1 \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "A mesmerising video of a deep sea jellyfish moving through an inky-black ocean. The jellyfish glows softly with an amber bioluminescence. The overall scene is lifelike.",
     "image_url": "https://storage.googleapis.com/falserverless/framepack/framepack.jpg"
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
    "fal-ai/framepack/f1",
    arguments={
        "prompt": "A mesmerising video of a deep sea jellyfish moving through an inky-black ocean. The jellyfish glows softly with an amber bioluminescence. The overall scene is lifelike.",
        "image_url": "https://storage.googleapis.com/falserverless/framepack/framepack.jpg"
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

const result = await fal.subscribe("fal-ai/framepack/f1", {
  input: {
    prompt: "A mesmerising video of a deep sea jellyfish moving through an inky-black ocean. The jellyfish glows softly with an amber bioluminescence. The overall scene is lifelike.",
    image_url: "https://storage.googleapis.com/falserverless/framepack/framepack.jpg"
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

- [Model Playground](https://fal.ai/models/fal-ai/framepack/f1)
- [API Documentation](https://fal.ai/models/fal-ai/framepack/f1/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/framepack/f1)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
