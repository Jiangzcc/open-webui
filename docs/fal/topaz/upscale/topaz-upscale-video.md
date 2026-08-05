# Topaz Video Upscale

> Professional-grade video upscaling using Topaz technology. Enhance your videos with high-quality upscaling.


## Overview

- **Endpoint**: `https://fal.run/fal-ai/topaz/upscale/video`
- **Model ID**: `fal-ai/topaz/upscale/video`
- **Category**: video-to-video
- **Kind**: inference
**Tags**: upscaling, high-res



## Pricing

For every second a video your request will cost **$0.01** for up to **720p**, **$0.02** for **720p** to **1080p**, and **$0.08** for above **1080p** output. Price doubles for **60fps** output. For **Gaia 2** output costs half of the prices.

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`video_url`** (`string`, _required_):
  URL of the video to upscale
  - Examples: "https://v3.fal.media/files/kangaroo/y5-1YTGpun17eSeggZMzX_video-1733468228.mp4"

- **`model`** (`ModelEnum`, _optional_):
  Video enhancement model, grouped by family. Precision — Proteus fits most footage, Artemis denoises and sharpens degraded sources, Gaia HQ/CG refine rendered content, Gaia 2 handles animation and motion graphics at 2x. Denoise — Nyx models are dedicated noise reduction. Generative — Starlight models use diffusion for restoration and upscaling. Starlight Precise 1, Starlight Precise 2 and Starlight Fast 1 are deprecated by Topaz; prefer Starlight Precise 2.5 or Starlight Fast 2. Default value: `"Proteus"`
  - Default: `"Proteus"`
  - Options: `"Proteus"`, `"Artemis HQ"`, `"Artemis MQ"`, `"Artemis LQ"`, `"Gaia HQ"`, `"Gaia CG"`, `"Gaia 2"`, `"Nyx"`, `"Nyx Fast"`, `"Nyx XL"`, `"Nyx HF"`, `"Starlight Precise 2.5"`, `"Starlight HQ"`, `"Starlight Mini"`, `"Starlight Sharp"`, `"Starlight Fast 2"`, `"Starlight Precise 1"`, `"Starlight Precise 2"`, `"Starlight Fast 1"`

- **`upscale_factor`** (`float`, _optional_):
  Factor to upscale the video by (e.g. 2.0 doubles width and height) Default value: `2`
  - Default: `2`
  - Range: `1` to `4`

- **`target_fps`** (`integer`, _optional_):
  Target FPS for frame interpolation. If set, frame interpolation will be enabled.
  - Range: `16` to `60`

- **`compression`** (`float`, _optional_):
  Compression artifact removal level (0.0-1.0). Default varies by model.
  - Range: `0` to `1`

- **`noise`** (`float`, _optional_):
  Noise reduction level (0.0-1.0). Default varies by model.
  - Range: `0` to `1`

- **`halo`** (`float`, _optional_):
  Halo reduction level (0.0-1.0). Default varies by model.
  - Range: `0` to `1`

- **`grain`** (`float`, _optional_):
  Film grain amount (0.0-0.1). Default varies by model.
  - Range: `0` to `0.1`, step: `0.01`

- **`recover_detail`** (`float`, _optional_):
  Recover original detail level (0.0-1.0). Higher values preserve more original detail.
  - Range: `0` to `1`

- **`H264_output`** (`boolean`, _optional_):
  Whether to use H264 codec for output video. Default is H265.
  - Default: `false`



**Required Parameters Example**:

```json
{
  "video_url": "https://v3.fal.media/files/kangaroo/y5-1YTGpun17eSeggZMzX_video-1733468228.mp4"
}
```

**Full Example**:

```json
{
  "video_url": "https://v3.fal.media/files/kangaroo/y5-1YTGpun17eSeggZMzX_video-1733468228.mp4",
  "model": "Proteus",
  "upscale_factor": 2
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`File`, _required_):
  The upscaled video file
  - Examples: {"url":"https://v3.fal.media/files/penguin/ztj_LB4gQlW6HIfVs8zX4_upscaled.mp4"}



**Example Response**:

```json
{
  "video": {
    "url": "https://v3.fal.media/files/penguin/ztj_LB4gQlW6HIfVs8zX4_upscaled.mp4"
  }
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/topaz/upscale/video \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "video_url": "https://v3.fal.media/files/kangaroo/y5-1YTGpun17eSeggZMzX_video-1733468228.mp4"
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
    "fal-ai/topaz/upscale/video",
    arguments={
        "video_url": "https://v3.fal.media/files/kangaroo/y5-1YTGpun17eSeggZMzX_video-1733468228.mp4"
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

const result = await fal.subscribe("fal-ai/topaz/upscale/video", {
  input: {
    video_url: "https://v3.fal.media/files/kangaroo/y5-1YTGpun17eSeggZMzX_video-1733468228.mp4"
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

- [Model Playground](https://fal.ai/models/fal-ai/topaz/upscale/video)
- [API Documentation](https://fal.ai/models/fal-ai/topaz/upscale/video/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/topaz/upscale/video)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
