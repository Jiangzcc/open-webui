# PixVerse C1 Image To Video

> Animate images into cinematic videos with PixVerse C1, supporting 1080p resolution and native audio generation.


## Overview

- **Endpoint**: `https://fal.run/fal-ai/pixverse/c1/image-to-video`
- **Model ID**: `fal-ai/pixverse/c1/image-to-video`
- **Category**: image-to-video
- **Kind**: inference
**Tags**: video-generation, image-to-video, pixverse, animation, 1080p, audio



## Pricing

Billing is calculated per second of video generated. For 360p, your request will cost **$0.030** per second without audio and **$0.040** per second with audio. For 540p, it will cost **$0.040** per second without audio and **$0.050** per second with audio. For 720p, it will cost **$0.050** per second without audio and **$0.065** per second with audio. For 1080p, it will cost **$0.095** per second without audio and **$0.120** per second with audio. For **$1** you can run this model for approximately **33 seconds** at 360p (no audio) or about **10 seconds** at 1080p (no audio).

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _required_):
  Text prompt for the video generation. Limited to 2048 UTF-8 encoded bytes. Because the limit counts bytes rather than characters, emoji and non-Latin or accented characters (which use multiple bytes each) can push a visually short prompt over the cap.
  - Examples: "A woman warrior with her hammer walking with his glacier wolf."

- **`resolution`** (`ResolutionEnum`, _optional_):
  The resolution of the generated video Default value: `"720p"`
  - Default: `"720p"`
  - Options: `"360p"`, `"540p"`, `"720p"`, `"1080p"`

- **`duration`** (`integer`, _optional_):
  The duration of the generated video in seconds (1-15) Default value: `5`
  - Default: `5`
  - Range: `1` to `15`

- **`seed`** (`integer`, _optional_):
  The same seed and the same prompt given to the same version of the model
  will output the same video every time.

- **`generate_audio_switch`** (`boolean`, _optional_):
  Enable audio generation (BGM, SFX, dialogue)
  - Default: `false`

- **`image_url`** (`string`, _required_):
  URL of the image to use as the first frame
  - Examples: "https://v3.fal.media/files/zebra/qL93Je8ezvzQgDOEzTjKF_KhGKZTEebZcDw6T5rwQPK_output.png"



**Required Parameters Example**:

```json
{
  "prompt": "A woman warrior with her hammer walking with his glacier wolf.",
  "image_url": "https://v3.fal.media/files/zebra/qL93Je8ezvzQgDOEzTjKF_KhGKZTEebZcDw6T5rwQPK_output.png"
}
```

**Full Example**:

```json
{
  "prompt": "A woman warrior with her hammer walking with his glacier wolf.",
  "resolution": "720p",
  "duration": 5,
  "image_url": "https://v3.fal.media/files/zebra/qL93Je8ezvzQgDOEzTjKF_KhGKZTEebZcDw6T5rwQPK_output.png"
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`File`, _required_):
  The generated video file.



**Example Response**:

```json
{
  "video": {
    "url": "",
    "content_type": "image/png",
    "file_name": "z9RV14K95DvU.png",
    "file_size": 4404019
  }
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/pixverse/c1/image-to-video \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "A woman warrior with her hammer walking with his glacier wolf.",
     "image_url": "https://v3.fal.media/files/zebra/qL93Je8ezvzQgDOEzTjKF_KhGKZTEebZcDw6T5rwQPK_output.png"
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
    "fal-ai/pixverse/c1/image-to-video",
    arguments={
        "prompt": "A woman warrior with her hammer walking with his glacier wolf.",
        "image_url": "https://v3.fal.media/files/zebra/qL93Je8ezvzQgDOEzTjKF_KhGKZTEebZcDw6T5rwQPK_output.png"
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

const result = await fal.subscribe("fal-ai/pixverse/c1/image-to-video", {
  input: {
    prompt: "A woman warrior with her hammer walking with his glacier wolf.",
    image_url: "https://v3.fal.media/files/zebra/qL93Je8ezvzQgDOEzTjKF_KhGKZTEebZcDw6T5rwQPK_output.png"
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

- [Model Playground](https://fal.ai/models/fal-ai/pixverse/c1/image-to-video)
- [API Documentation](https://fal.ai/models/fal-ai/pixverse/c1/image-to-video/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/pixverse/c1/image-to-video)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
