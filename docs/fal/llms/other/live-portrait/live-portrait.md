# Live Portrait

> Transfer expression from a video to a portrait.


## Overview

- **Endpoint**: `https://fal.run/fal-ai/live-portrait`
- **Model ID**: `fal-ai/live-portrait`
- **Category**: image-to-video
- **Kind**: inference
**Tags**: expression, animation



## Pricing

- **Price**: $0 per compute seconds

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`video_url`** (`string`, _required_):
  URL of the video to drive the lip syncing.
  - Examples: "https://storage.googleapis.com/falserverless/model_tests/live-portrait/liveportrait-example.mp4"

- **`image_url`** (`string`, _required_):
  URL of the image to be animated
  - Examples: "https://storage.googleapis.com/falserverless/model_tests/live-portrait/XKEmk3mAzGHUjK3qqH-UL.jpeg"

- **`blink`** (`float`, _optional_):
  Amount to blink the eyes
  - Default: `0`
  - Range: `-30` to `30`

- **`eyebrow`** (`float`, _optional_):
  Amount to raise or lower eyebrows
  - Default: `0`
  - Range: `-30` to `30`

- **`wink`** (`float`, _optional_):
  Amount to wink
  - Default: `0`
  - Range: `0` to `25`

- **`pupil_x`** (`float`, _optional_):
  Amount to move pupils horizontally
  - Default: `0`
  - Range: `-45` to `45`

- **`pupil_y`** (`float`, _optional_):
  Amount to move pupils vertically
  - Default: `0`
  - Range: `-45` to `45`

- **`aaa`** (`float`, _optional_):
  Amount to open mouth in 'aaa' shape
  - Default: `0`
  - Range: `-200` to `200`

- **`eee`** (`float`, _optional_):
  Amount to shape mouth in 'eee' position
  - Default: `0`
  - Range: `-40` to `40`

- **`woo`** (`float`, _optional_):
  Amount to shape mouth in 'woo' position
  - Default: `0`
  - Range: `-100` to `100`

- **`smile`** (`float`, _optional_):
  Amount to smile
  - Default: `0`
  - Range: `-2` to `2`

- **`flag_lip_zero`** (`boolean`, _optional_):
  Whether to set the lip to closed state before animation. Only takes effect when flag_eye_retargeting and flag_lip_retargeting are False. Default value: `true`
  - Default: `true`

- **`rotate_pitch`** (`float`, _optional_):
  Amount to rotate the face in pitch
  - Default: `0`
  - Range: `-45` to `45`

- **`rotate_yaw`** (`float`, _optional_):
  Amount to rotate the face in yaw
  - Default: `0`
  - Range: `-45` to `45`

- **`rotate_roll`** (`float`, _optional_):
  Amount to rotate the face in roll
  - Default: `0`
  - Range: `-45` to `45`

- **`flag_eye_retargeting`** (`boolean`, _optional_):
  Whether to enable eye retargeting.
  - Default: `false`

- **`flag_lip_retargeting`** (`boolean`, _optional_):
  Whether to enable lip retargeting.
  - Default: `false`

- **`flag_stitching`** (`boolean`, _optional_):
  Whether to enable stitching. Recommended to set to True. Default value: `true`
  - Default: `true`

- **`flag_relative`** (`boolean`, _optional_):
  Whether to use relative motion. Default value: `true`
  - Default: `true`

- **`flag_pasteback`** (`boolean`, _optional_):
  Whether to paste-back/stitch the animated face cropping from the face-cropping space to the original image space. Default value: `true`
  - Default: `true`

- **`flag_do_crop`** (`boolean`, _optional_):
  Whether to crop the source portrait to the face-cropping space. Default value: `true`
  - Default: `true`

- **`flag_do_rot`** (`boolean`, _optional_):
  Whether to conduct the rotation when flag_do_crop is True. Default value: `true`
  - Default: `true`

- **`dsize`** (`integer`, _optional_):
  Size of the output image. Default value: `512`
  - Default: `512`

- **`scale`** (`float`, _optional_):
  Scaling factor for the face crop. Default value: `2.3`
  - Default: `2.3`

- **`vx_ratio`** (`float`, _optional_):
  Horizontal offset ratio for face crop.
  - Default: `0`

- **`vy_ratio`** (`float`, _optional_):
  Vertical offset ratio for face crop. Positive values move up, negative values move down. Default value: `-0.125`
  - Default: `-0.125`

- **`batch_size`** (`integer`, _optional_):
  Batch size for the model. The larger the batch size, the faster the model will run, but the more memory it will consume. Default value: `32`
  - Default: `32`

- **`enable_safety_checker`** (`boolean`, _optional_):
  Whether to enable the safety checker. If enabled, the model will check if the input image contains a face before processing it.
  The safety checker will process the input image
  - Default: `false`



**Required Parameters Example**:

```json
{
  "video_url": "https://storage.googleapis.com/falserverless/model_tests/live-portrait/liveportrait-example.mp4",
  "image_url": "https://storage.googleapis.com/falserverless/model_tests/live-portrait/XKEmk3mAzGHUjK3qqH-UL.jpeg"
}
```

**Full Example**:

```json
{
  "video_url": "https://storage.googleapis.com/falserverless/model_tests/live-portrait/liveportrait-example.mp4",
  "image_url": "https://storage.googleapis.com/falserverless/model_tests/live-portrait/XKEmk3mAzGHUjK3qqH-UL.jpeg",
  "flag_lip_zero": true,
  "flag_stitching": true,
  "flag_relative": true,
  "flag_pasteback": true,
  "flag_do_crop": true,
  "flag_do_rot": true,
  "dsize": 512,
  "scale": 2.3,
  "vy_ratio": -0.125,
  "batch_size": 32
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
  --url https://fal.run/fal-ai/live-portrait \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "video_url": "https://storage.googleapis.com/falserverless/model_tests/live-portrait/liveportrait-example.mp4",
     "image_url": "https://storage.googleapis.com/falserverless/model_tests/live-portrait/XKEmk3mAzGHUjK3qqH-UL.jpeg"
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
    "fal-ai/live-portrait",
    arguments={
        "video_url": "https://storage.googleapis.com/falserverless/model_tests/live-portrait/liveportrait-example.mp4",
        "image_url": "https://storage.googleapis.com/falserverless/model_tests/live-portrait/XKEmk3mAzGHUjK3qqH-UL.jpeg"
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

const result = await fal.subscribe("fal-ai/live-portrait", {
  input: {
    video_url: "https://storage.googleapis.com/falserverless/model_tests/live-portrait/liveportrait-example.mp4",
    image_url: "https://storage.googleapis.com/falserverless/model_tests/live-portrait/XKEmk3mAzGHUjK3qqH-UL.jpeg"
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

- [Model Playground](https://fal.ai/models/fal-ai/live-portrait)
- [API Documentation](https://fal.ai/models/fal-ai/live-portrait/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/live-portrait)
- [GitHub Repository](https://github.com/KwaiVGI/LivePortrait/blob/main/LICENSE)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
