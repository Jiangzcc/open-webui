# Depth Anything Video

> Generates depth maps from video using Video Depth Anything (CVPR 2025). Produces per-frame depth estimation with temporal consistency across frames. Supports 3 model sizes (Small, Base, Large), 5 colormaps including grayscale, side-by-side comparison with the original video, and raw depth export as .npz. Useful for 3D reconstruction, video effects, compositing, and scene understanding.    


## Overview

- **Endpoint**: `https://fal.run/fal-ai/depth-anything-video`
- **Model ID**: `fal-ai/depth-anything-video`
- **Category**: video-to-video
- **Kind**: inference
**Tags**: video to video, motion, edit



## Pricing

Your request will cost $0.04 per second of video.

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`video_url`** (`string`, _required_):
  URL of the input video to estimate depth for.
  - Examples: "https://v3b.fal.media/files/b/0a8fb1c1/xNTrr7wtczzLBkJdyE5_f_7JTYCmQe.mp4"

- **`model`** (`ModelEnum`, _optional_):
  Depth estimation model size. VDA-Large = best quality, VDA-Small = fastest. Default value: `"VDA-Large"`
  - Default: `"VDA-Large"`
  - Options: `"VDA-Small"`, `"VDA-Base"`, `"VDA-Large"`

- **`colormap`** (`ColormapEnum`, _optional_):
  Colormap for depth visualization. 'turbo' (recommended) shows near=warm, far=cool. 'grayscale' for raw normalized depth. 'inferno'/'magma' for perceptually uniform. 'viridis' for colorblind-friendly. Default value: `"grayscale"`
  - Default: `"grayscale"`
  - Options: `"grayscale"`, `"turbo"`, `"inferno"`, `"magma"`, `"viridis"`

- **`resolution`** (`ResolutionEnum`, _optional_):
  Output resolution. 'auto' preserves input (max 1080p). Options: 'auto', '360p', '480p', '720p', '1080p'. Default value: `"auto"`
  - Default: `"auto"`
  - Options: `"auto"`, `"360p"`, `"480p"`, `"720p"`, `"1080p"`

- **`max_frames`** (`integer`, _optional_):
  Max frames to process (max 2400). None = up to 2400.

- **`output_fps`** (`float`, _optional_):
  Output video FPS. None = same as input.

- **`side_by_side`** (`boolean`, _optional_):
  Output original | depth comparison video.
  - Default: `false`

- **`include_raw_depths`** (`boolean`, _optional_):
  Export raw float32 depths as .npz file with: 'depths' [N,H,W], 'min_depth', 'max_depth', 'fps', 'model', 'shape'.
  - Default: `false`



**Required Parameters Example**:

```json
{
  "video_url": "https://v3b.fal.media/files/b/0a8fb1c1/xNTrr7wtczzLBkJdyE5_f_7JTYCmQe.mp4"
}
```

**Full Example**:

```json
{
  "video_url": "https://v3b.fal.media/files/b/0a8fb1c1/xNTrr7wtczzLBkJdyE5_f_7JTYCmQe.mp4",
  "model": "VDA-Large",
  "colormap": "grayscale",
  "resolution": "auto"
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`File`, _required_):
  Depth visualization video (MP4, H.264).
  - Examples: {"url":"https://v3b.fal.media/files/b/0a909a72/bC4JmEhmaBIaMC4vRhhTq_depth_output.mp4"}

- **`raw_depths`** (`File`, _optional_):
  Raw depth values as .npz (if include_raw_depths=True).



**Example Response**:

```json
{
  "video": {
    "url": "https://v3b.fal.media/files/b/0a909a72/bC4JmEhmaBIaMC4vRhhTq_depth_output.mp4"
  }
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/depth-anything-video \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "video_url": "https://v3b.fal.media/files/b/0a8fb1c1/xNTrr7wtczzLBkJdyE5_f_7JTYCmQe.mp4"
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
    "fal-ai/depth-anything-video",
    arguments={
        "video_url": "https://v3b.fal.media/files/b/0a8fb1c1/xNTrr7wtczzLBkJdyE5_f_7JTYCmQe.mp4"
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

const result = await fal.subscribe("fal-ai/depth-anything-video", {
  input: {
    video_url: "https://v3b.fal.media/files/b/0a8fb1c1/xNTrr7wtczzLBkJdyE5_f_7JTYCmQe.mp4"
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

- [Model Playground](https://fal.ai/models/fal-ai/depth-anything-video)
- [API Documentation](https://fal.ai/models/fal-ai/depth-anything-video/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/depth-anything-video)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
