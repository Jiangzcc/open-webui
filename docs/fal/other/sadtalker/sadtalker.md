# Sad Talker

> Learning Realistic 3D Motion Coefficients for Stylized Audio-Driven Single Image Talking Face Animation


## Overview

- **Endpoint**: `https://fal.run/fal-ai/sadtalker`
- **Model ID**: `fal-ai/sadtalker`
- **Category**: image-to-video
- **Kind**: inference
**Tags**: animation



## Pricing

- **Price**: $0 per compute seconds

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`source_image_url`** (`string`, _required_):
  URL of the source image
  - Examples: "https://storage.googleapis.com/falserverless/model_tests/sadtalker/anime_girl.png"

- **`driven_audio_url`** (`string`, _required_):
  URL of the driven audio
  - Examples: "https://storage.googleapis.com/falserverless/model_tests/sadtalker/deyu.wav"

- **`pose_style`** (`integer`, _optional_):
  The style of the pose
  - Default: `0`
  - Range: `0` to `45`

- **`face_model_resolution`** (`FaceModelResolutionEnum`, _optional_):
  The resolution of the face model Default value: `"256"`
  - Default: `"256"`
  - Options: `"256"`, `"512"`

- **`expression_scale`** (`float`, _optional_):
  The scale of the expression Default value: `1`
  - Default: `1`
  - Range: `0` to `3`, step: `0.1`

- **`face_enhancer`** (`string`, _optional_):
  The type of face enhancer to use
  - Examples: null

- **`still_mode`** (`boolean`, _optional_):
  Whether to use still mode. Fewer head motion, works with preprocess `full`.
  - Default: `false`

- **`preprocess`** (`PreprocessEnum`, _optional_):
  The type of preprocessing to use Default value: `"crop"`
  - Default: `"crop"`
  - Options: `"crop"`, `"extcrop"`, `"resize"`, `"full"`, `"extfull"`



**Required Parameters Example**:

```json
{
  "source_image_url": "https://storage.googleapis.com/falserverless/model_tests/sadtalker/anime_girl.png",
  "driven_audio_url": "https://storage.googleapis.com/falserverless/model_tests/sadtalker/deyu.wav"
}
```

**Full Example**:

```json
{
  "source_image_url": "https://storage.googleapis.com/falserverless/model_tests/sadtalker/anime_girl.png",
  "driven_audio_url": "https://storage.googleapis.com/falserverless/model_tests/sadtalker/deyu.wav",
  "face_model_resolution": "256",
  "expression_scale": 1,
  "face_enhancer": null,
  "preprocess": "crop"
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`File`, _required_):
  URL of the generated video



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
  --url https://fal.run/fal-ai/sadtalker \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "source_image_url": "https://storage.googleapis.com/falserverless/model_tests/sadtalker/anime_girl.png",
     "driven_audio_url": "https://storage.googleapis.com/falserverless/model_tests/sadtalker/deyu.wav"
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
    "fal-ai/sadtalker",
    arguments={
        "source_image_url": "https://storage.googleapis.com/falserverless/model_tests/sadtalker/anime_girl.png",
        "driven_audio_url": "https://storage.googleapis.com/falserverless/model_tests/sadtalker/deyu.wav"
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

const result = await fal.subscribe("fal-ai/sadtalker", {
  input: {
    source_image_url: "https://storage.googleapis.com/falserverless/model_tests/sadtalker/anime_girl.png",
    driven_audio_url: "https://storage.googleapis.com/falserverless/model_tests/sadtalker/deyu.wav"
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

- [Model Playground](https://fal.ai/models/fal-ai/sadtalker)
- [API Documentation](https://fal.ai/models/fal-ai/sadtalker/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/sadtalker)
- [GitHub Repository](https://github.com/OpenTalker/SadTalker/blob/main/LICENSE)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
