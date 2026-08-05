# Lightx

> Use tlightx capabilities to relight and recamera your videos.


## Overview

- **Endpoint**: `https://fal.run/fal-ai/lightx/relight`
- **Model ID**: `fal-ai/lightx/relight`
- **Category**: video-to-video
- **Kind**: inference
**Tags**: video-to-video



## Pricing

Your request will cost **0.1$** per output video second.

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`video_url`** (`string`, _required_):
  URL of the input video.
  - Examples: "https://storage.googleapis.com/falserverless/example_inputs/lightx_video.mp4"

- **`prompt`** (`string`, _optional_):
  Optional text prompt. If omitted, Light-X will auto-caption the video.

- **`seed`** (`integer`, _optional_):
  Random seed for reproducibility. If None, a random seed is chosen.

- **`relit_cond_type`** (`RelitCondTypeEnum`, _optional_):
  Relight condition type. Default value: `"ic"`
  - Default: `"ic"`
  - Options: `"ic"`, `"ref"`, `"hdr"`, `"bg"`

- **`relight_parameters`** (`RelightParameters`, _optional_):
  Relighting parameters (required for relight_condition_type='ic'). Not used for 'bg' (which expects a background image URL instead).
  - Examples: {"use_sky_mask":false,"cfg":2,"relight_prompt":"Sunlight","bg_source":"Right"}

- **`relit_cond_img_url`** (`string`, _optional_):
  URL of conditioning image. Required for relight_condition_type='ref'/'hdr'. Also required for relight_condition_type='bg' (background image).
  - Examples: "https://storage.googleapis.com/falserverless/example_inputs/lightx_image.png"

- **`ref_id`** (`integer`, _optional_):
  Frame index to use as reference to relight the video with reference. Must be less than the number of generated frames (default 49).
  - Default: `0`
  - Range: `0` to `48`



**Required Parameters Example**:

```json
{
  "video_url": "https://storage.googleapis.com/falserverless/example_inputs/lightx_video.mp4"
}
```

**Full Example**:

```json
{
  "video_url": "https://storage.googleapis.com/falserverless/example_inputs/lightx_video.mp4",
  "relit_cond_type": "ic",
  "relight_parameters": {
    "use_sky_mask": false,
    "cfg": 2,
    "relight_prompt": "Sunlight",
    "bg_source": "Right"
  },
  "relit_cond_img_url": "https://storage.googleapis.com/falserverless/example_inputs/lightx_image.png"
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`File`, _required_):
  The generated video file.
  - Examples: "https://v3b.fal.media/files/b/0a8715c9/x378fHboeiGD6j_0nbWlJ_gen.mp4"

- **`seed`** (`integer`, _required_):
  The seed used for generation.

- **`input_video`** (`File`, _optional_):
  Optional: normalized/processed input video (if produced by the pipeline).

- **`viz_video`** (`File`, _optional_):
  Optional: visualization/debug video (if produced by the pipeline).



**Example Response**:

```json
{
  "video": "https://v3b.fal.media/files/b/0a8715c9/x378fHboeiGD6j_0nbWlJ_gen.mp4"
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/lightx/relight \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "video_url": "https://storage.googleapis.com/falserverless/example_inputs/lightx_video.mp4"
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
    "fal-ai/lightx/relight",
    arguments={
        "video_url": "https://storage.googleapis.com/falserverless/example_inputs/lightx_video.mp4"
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

const result = await fal.subscribe("fal-ai/lightx/relight", {
  input: {
    video_url: "https://storage.googleapis.com/falserverless/example_inputs/lightx_video.mp4"
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

- [Model Playground](https://fal.ai/models/fal-ai/lightx/relight)
- [API Documentation](https://fal.ai/models/fal-ai/lightx/relight/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/lightx/relight)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
