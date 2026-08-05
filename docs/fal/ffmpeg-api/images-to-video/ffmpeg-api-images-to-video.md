# Ffmpeg Api Images to Video

> A fal.ai endpoint that stitches an ordered list of images into an MP4 video by holding each image for a specified number of frames at a configurable frame rate


## Overview

- **Endpoint**: `https://fal.run/fal-ai/ffmpeg-api/images-to-video`
- **Model ID**: `fal-ai/ffmpeg-api/images-to-video`
- **Category**: image-to-video
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


- **`images`** (`list<ImageFrame>`, _required_):
  Ordered list of images to play as video frames. Each image is held for its specified number of frames before cutting to the next image.
  - Array of ImageFrame
  - Examples: [{"frames":4,"url":"https://v3.fal.media/files/koala/oei_-iPIYFnhdB8SxojND_qwen-edit-res.png"},{"frames":2,"url":"https://v3.fal.media/files/tiger/c8VSfX5XtJ3DCzV-4Bxg8_kid_image.png"},{"frames":4,"url":"https://v3.fal.media/files/koala/oei_-iPIYFnhdB8SxojND_qwen-edit-res.png"}]

- **`fps`** (`float`, _optional_):
  Frames per second of the output video. Default value: `24`
  - Default: `24`
  - Range: `1` to `120`



**Required Parameters Example**:

```json
{
  "images": [
    {
      "frames": 4,
      "url": "https://v3.fal.media/files/koala/oei_-iPIYFnhdB8SxojND_qwen-edit-res.png"
    },
    {
      "frames": 2,
      "url": "https://v3.fal.media/files/tiger/c8VSfX5XtJ3DCzV-4Bxg8_kid_image.png"
    },
    {
      "frames": 4,
      "url": "https://v3.fal.media/files/koala/oei_-iPIYFnhdB8SxojND_qwen-edit-res.png"
    }
  ]
}
```

**Full Example**:

```json
{
  "images": [
    {
      "frames": 4,
      "url": "https://v3.fal.media/files/koala/oei_-iPIYFnhdB8SxojND_qwen-edit-res.png"
    },
    {
      "frames": 2,
      "url": "https://v3.fal.media/files/tiger/c8VSfX5XtJ3DCzV-4Bxg8_kid_image.png"
    },
    {
      "frames": 4,
      "url": "https://v3.fal.media/files/koala/oei_-iPIYFnhdB8SxojND_qwen-edit-res.png"
    }
  ],
  "fps": 24
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`File`, _required_):
  Output MP4 video.



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
  --url https://fal.run/fal-ai/ffmpeg-api/images-to-video \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "images": [
       {
         "frames": 4,
         "url": "https://v3.fal.media/files/koala/oei_-iPIYFnhdB8SxojND_qwen-edit-res.png"
       },
       {
         "frames": 2,
         "url": "https://v3.fal.media/files/tiger/c8VSfX5XtJ3DCzV-4Bxg8_kid_image.png"
       },
       {
         "frames": 4,
         "url": "https://v3.fal.media/files/koala/oei_-iPIYFnhdB8SxojND_qwen-edit-res.png"
       }
     ]
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
    "fal-ai/ffmpeg-api/images-to-video",
    arguments={
        "images": [{
            "frames": 4,
            "url": "https://v3.fal.media/files/koala/oei_-iPIYFnhdB8SxojND_qwen-edit-res.png"
        }, {
            "frames": 2,
            "url": "https://v3.fal.media/files/tiger/c8VSfX5XtJ3DCzV-4Bxg8_kid_image.png"
        }, {
            "frames": 4,
            "url": "https://v3.fal.media/files/koala/oei_-iPIYFnhdB8SxojND_qwen-edit-res.png"
        }]
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

const result = await fal.subscribe("fal-ai/ffmpeg-api/images-to-video", {
  input: {
    images: [{
      frames: 4,
      url: "https://v3.fal.media/files/koala/oei_-iPIYFnhdB8SxojND_qwen-edit-res.png"
    }, {
      frames: 2,
      url: "https://v3.fal.media/files/tiger/c8VSfX5XtJ3DCzV-4Bxg8_kid_image.png"
    }, {
      frames: 4,
      url: "https://v3.fal.media/files/koala/oei_-iPIYFnhdB8SxojND_qwen-edit-res.png"
    }]
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

- [Model Playground](https://fal.ai/models/fal-ai/ffmpeg-api/images-to-video)
- [API Documentation](https://fal.ai/models/fal-ai/ffmpeg-api/images-to-video/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/ffmpeg-api/images-to-video)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
