# Birefnet

> Video background removal version of bilateral reference framework (BiRefNet) for high-resolution dichotomous image segmentation (DIS)



## Overview

- **Endpoint**: `https://fal.run/fal-ai/birefnet/v2/video`
- **Model ID**: `fal-ai/birefnet/v2/video`
- **Category**: video-to-video
- **Kind**: inference
**Tags**: utility, editing



## Pricing

- **Price**: $0 per compute seconds

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`model`** (`ModelEnum`, _optional_):
  Model to use for background removal.
  The 'General Use (Light)' model is the original model used in the BiRefNet repository.
  The 'General Use (Light 2K)' model is the original model used in the BiRefNet repository but trained with 2K images.
  The 'General Use (Heavy)' model is a slower but more accurate model.
  The 'Matting' model is a model trained specifically for matting images.
  The 'Portrait' model is a model trained specifically for portrait images.
  The 'General Use (Dynamic)' model supports dynamic resolutions from 256x256 to 2304x2304.
  The 'General Use (Light)' model is recommended for most use cases.
  
  The corresponding models are as follows:
  - 'General Use (Light)': BiRefNet
  - 'General Use (Light 2K)': BiRefNet_lite-2K
  - 'General Use (Heavy)': BiRefNet_lite
  - 'Matting': BiRefNet-matting
  - 'Portrait': BiRefNet-portrait
  - 'General Use (Dynamic)': BiRefNet_dynamic Default value: `"General Use (Light)"`
  - Default: `"General Use (Light)"`
  - Options: `"General Use (Light)"`, `"General Use (Light 2K)"`, `"General Use (Heavy)"`, `"Matting"`, `"Portrait"`, `"General Use (Dynamic)"`

- **`operating_resolution`** (`OperatingResolutionEnum`, _optional_):
  The resolution to operate on. The higher the resolution, the more accurate the output will be for high res input images. The '2304x2304' option is only available for the 'General Use (Dynamic)' model. Default value: `"1024x1024"`
  - Default: `"1024x1024"`
  - Options: `"1024x1024"`, `"2048x2048"`, `"2304x2304"`

- **`output_mask`** (`boolean`, _optional_):
  Whether to output the mask used to remove the background
  - Default: `false`

- **`refine_foreground`** (`boolean`, _optional_):
  Whether to refine the foreground using the estimated mask Default value: `true`
  - Default: `true`

- **`sync_mode`** (`boolean`, _optional_):
  If `True`, the media will be returned as a data URI and the output data won't be available in the request history.
  - Default: `false`

- **`video_url`** (`string`, _required_):
  URL of the video to remove background from
  - Examples: "https://storage.googleapis.com/falserverless/example_inputs/birefnet-video-input.mp4"

- **`video_output_type`** (`VideoOutputTypeEnum`, _optional_):
  The output type of the generated video. Default value: `"X264 (.mp4)"`
  - Default: `"X264 (.mp4)"`
  - Options: `"X264 (.mp4)"`, `"VP9 (.webm)"`, `"PRORES4444 (.mov)"`, `"GIF (.gif)"`

- **`video_quality`** (`VideoQualityEnum`, _optional_):
  The quality of the generated video. Default value: `"high"`
  - Default: `"high"`
  - Options: `"low"`, `"medium"`, `"high"`, `"maximum"`

- **`video_write_mode`** (`VideoWriteModeEnum`, _optional_):
  The write mode of the generated video. Default value: `"balanced"`
  - Default: `"balanced"`
  - Options: `"fast"`, `"balanced"`, `"small"`



**Required Parameters Example**:

```json
{
  "video_url": "https://storage.googleapis.com/falserverless/example_inputs/birefnet-video-input.mp4"
}
```

**Full Example**:

```json
{
  "model": "General Use (Light)",
  "operating_resolution": "1024x1024",
  "refine_foreground": true,
  "video_url": "https://storage.googleapis.com/falserverless/example_inputs/birefnet-video-input.mp4",
  "video_output_type": "X264 (.mp4)",
  "video_quality": "high",
  "video_write_mode": "balanced"
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`VideoFile`, _required_):
  Video with background removed
  - Examples: {"file_name":"birefnet-video-output.webm","url":"https://storage.googleapis.com/falserverless/example_outputs/birefnet-video-output.webm","num_frames":192,"height":1080,"width":1920,"fps":24,"duration":8,"content_type":"video/webm"}

- **`mask_video`** (`VideoFile`, _optional_):
  Mask used to remove the background



**Example Response**:

```json
{
  "video": {
    "file_name": "birefnet-video-output.webm",
    "url": "https://storage.googleapis.com/falserverless/example_outputs/birefnet-video-output.webm",
    "num_frames": 192,
    "height": 1080,
    "width": 1920,
    "fps": 24,
    "duration": 8,
    "content_type": "video/webm"
  }
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/birefnet/v2/video \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "video_url": "https://storage.googleapis.com/falserverless/example_inputs/birefnet-video-input.mp4"
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
    "fal-ai/birefnet/v2/video",
    arguments={
        "video_url": "https://storage.googleapis.com/falserverless/example_inputs/birefnet-video-input.mp4"
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

const result = await fal.subscribe("fal-ai/birefnet/v2/video", {
  input: {
    video_url: "https://storage.googleapis.com/falserverless/example_inputs/birefnet-video-input.mp4"
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

- [Model Playground](https://fal.ai/models/fal-ai/birefnet/v2/video)
- [API Documentation](https://fal.ai/models/fal-ai/birefnet/v2/video/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/birefnet/v2/video)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
