# Lightx

> Use the capabilities of lightx to relight and recamera your videos.


## Overview

- **Endpoint**: `https://fal.run/fal-ai/lightx/recamera`
- **Model ID**: `fal-ai/lightx/recamera`
- **Category**: video-to-video
- **Kind**: inference
**Tags**: video-to-video, recamera, relight



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

- **`camera`** (`CameraEnum`, _optional_):
  Camera control mode. Default value: `"traj"`
  - Default: `"traj"`
  - Options: `"traj"`, `"target"`

- **`mode`** (`ModeEnum`, _optional_):
  Camera motion mode. Default value: `"gradual"`
  - Default: `"gradual"`
  - Options: `"gradual"`, `"bullet"`, `"direct"`, `"dolly-zoom"`

- **`trajectory`** (`TrajectoryParameters`, _optional_):
  Camera trajectory parameters (required for recamera mode).
  - Examples: {"phi":[0,-3,-8,-15,-20,-15,-10,-5,0],"radius":[0,0.02,0.09,0.16,0.25,0.2,0.09,0],"theta":[0,2,8,10,5,3,0,-2,-5,-8,-5,-3,0]}

- **`target_pose`** (`list<float>`, _optional_):
  Target camera pose [theta, phi, radius, x, y] (required when camera='target').
  - Array of float
  - Examples: [10,-15,0.2,0,0]



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
  "camera": "traj",
  "mode": "gradual",
  "trajectory": {
    "phi": [
      0,
      -3,
      -8,
      -15,
      -20,
      -15,
      -10,
      -5,
      0
    ],
    "radius": [
      0,
      0.02,
      0.09,
      0.16,
      0.25,
      0.2,
      0.09,
      0
    ],
    "theta": [
      0,
      2,
      8,
      10,
      5,
      3,
      0,
      -2,
      -5,
      -8,
      -5,
      -3,
      0
    ]
  },
  "target_pose": [
    10,
    -15,
    0.2,
    0,
    0
  ]
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
  --url https://fal.run/fal-ai/lightx/recamera \
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
    "fal-ai/lightx/recamera",
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

const result = await fal.subscribe("fal-ai/lightx/recamera", {
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

- [Model Playground](https://fal.ai/models/fal-ai/lightx/recamera)
- [API Documentation](https://fal.ai/models/fal-ai/lightx/recamera/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/lightx/recamera)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
