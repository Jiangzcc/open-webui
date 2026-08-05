# Davinci Magihuman

> Expressive facial performance, natural speech-expression coordination, realistic body motion, and accurate audio-video synchronization with DaVinci-MagiHuman model


## Overview

- **Endpoint**: `https://fal.run/fal-ai/davinci-magihuman`
- **Model ID**: `fal-ai/davinci-magihuman`
- **Category**: image-to-video
- **Kind**: inference
**Tags**: animation, lip sync



## Pricing

- **Price**: $0.05 per seconds

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _required_):
  Text prompt describing the desired video content.
  - Examples: "A woman is walking through a metro station and says, 'I love walking through this station, it always feels so alive.'"

- **`image_url`** (`string`, _required_):
  URL of the reference image for image-to-video generation.
  - Examples: "https://v3b.fal.media/files/b/0a93a275/W1Nnkr552fPfcTuE2UgKL_Zmt1dxWICl_oX5nbuMVLQ.jpeg"

- **`audio_url`** (`string`, _optional_):
  Optional URL of the driving audio for lipsync mode. If omitted, audio is generated from the prompt.

- **`duration`** (`integer`, _optional_):
  Duration of the generated video in seconds. Default value: `5`
  - Default: `5`
  - Range: `1` to `30`

- **`resolution`** (`ResolutionEnum`, _optional_):
  Output resolution. '256p' uses the official base-model 448x256 path. '1080p' uses the official base + 1080p super-resolution pipeline. '540p' and '720p' reuse that sharper 1080p SR path and downsample to the requested output size. Default value: `"256p"`
  - Default: `"256p"`
  - Options: `"256p"`, `"540p"`, `"720p"`, `"1080p"`

- **`num_inference_steps`** (`integer`, _optional_):
  Number of denoising steps. Defaults to 8 for 256p and 32 for 540p/720p/1080p (base + SR).
  - Range: `1` to `50`

- **`guidance_scale`** (`float`, _optional_):
  Classifier-free guidance scale. Default value: `5`
  - Default: `5`
  - Range: `0` to `20`

- **`seed`** (`integer`, _optional_):
  Random seed for reproducibility.

- **`enable_safety_checker`** (`boolean`, _optional_):
  If enabled, runs safety checks on the prompt and input image. Default value: `true`
  - Default: `true`



**Required Parameters Example**:

```json
{
  "prompt": "A woman is walking through a metro station and says, 'I love walking through this station, it always feels so alive.'",
  "image_url": "https://v3b.fal.media/files/b/0a93a275/W1Nnkr552fPfcTuE2UgKL_Zmt1dxWICl_oX5nbuMVLQ.jpeg"
}
```

**Full Example**:

```json
{
  "prompt": "A woman is walking through a metro station and says, 'I love walking through this station, it always feels so alive.'",
  "image_url": "https://v3b.fal.media/files/b/0a93a275/W1Nnkr552fPfcTuE2UgKL_Zmt1dxWICl_oX5nbuMVLQ.jpeg",
  "duration": 5,
  "resolution": "256p",
  "guidance_scale": 5,
  "enable_safety_checker": true
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`File`, _optional_):
  The generated video with synchronized audio.

- **`seed`** (`integer`, _required_):
  The seed used for generation.



**Example Response**:

```json
{}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/davinci-magihuman \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "A woman is walking through a metro station and says, 'I love walking through this station, it always feels so alive.'",
     "image_url": "https://v3b.fal.media/files/b/0a93a275/W1Nnkr552fPfcTuE2UgKL_Zmt1dxWICl_oX5nbuMVLQ.jpeg"
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
    "fal-ai/davinci-magihuman",
    arguments={
        "prompt": "A woman is walking through a metro station and says, 'I love walking through this station, it always feels so alive.'",
        "image_url": "https://v3b.fal.media/files/b/0a93a275/W1Nnkr552fPfcTuE2UgKL_Zmt1dxWICl_oX5nbuMVLQ.jpeg"
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

const result = await fal.subscribe("fal-ai/davinci-magihuman", {
  input: {
    prompt: "A woman is walking through a metro station and says, 'I love walking through this station, it always feels so alive.'",
    image_url: "https://v3b.fal.media/files/b/0a93a275/W1Nnkr552fPfcTuE2UgKL_Zmt1dxWICl_oX5nbuMVLQ.jpeg"
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

- [Model Playground](https://fal.ai/models/fal-ai/davinci-magihuman)
- [API Documentation](https://fal.ai/models/fal-ai/davinci-magihuman/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/davinci-magihuman)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
