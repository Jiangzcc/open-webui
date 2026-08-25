# V2.6

> Wan 2.6 reference-to-video flash model.


## Overview

- **Endpoint**: `https://fal.run/wan/v2.6/reference-to-video/flash`
- **Model ID**: `wan/v2.6/reference-to-video/flash`
- **Category**: video-to-video
- **Kind**: inference
**Tags**: reference-to-video



## Pricing

Your request will cost  **$0.10** per second for **720p**, **$0.15** per second for **1080p**.

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _required_):
  Use Character1, Character2, etc. to reference subjects from your reference files. Works for people, animals, or objects. For multi-shot prompts: '[0-3s] Shot 1. [3-6s] Shot 2.' Max 1500 characters. Reference order: video_urls first, then image_urls.
  - Examples: "Dance battle between Character1 and Character2."

- **`video_urls`** (`list<string>`, _optional_):
  Reference videos for subject consistency (0-3 videos). Videos' FPS must be at least 16 FPS. Combined with image_urls, total references cannot exceed 5. Reference order: video_urls are numbered first (Character1, Character2...), then image_urls continue the sequence.
  - Array of string
  - Examples: ["https://v3b.fal.media/files/b/0a8d6d47/FtSBJGfZuivKfBIrRuWxa_video.mp4"]

- **`image_urls`** (`list<string>`, _optional_):
  Reference images for subject consistency (0-5 images). Combined with video_urls, total references cannot exceed 5. Formats: JPEG, JPG, PNG (no alpha), BMP, WEBP. Resolution: 240-5000px. Max 10MB each. Reference order: image_urls continue numbering after video_urls.
  - Array of string
  - Examples: ["https://v3b.fal.media/files/b/0a8d6d49/4XDgJcWQHLgkmUOL2JlPt_iXGPlm9y.png"]

- **`aspect_ratio`** (`AspectRatioEnum`, _optional_):
  The aspect ratio of the generated video. Default value: `"16:9"`
  - Default: `"16:9"`
  - Options: `"16:9"`, `"9:16"`, `"1:1"`, `"4:3"`, `"3:4"`

- **`resolution`** (`ResolutionEnum`, _optional_):
  Video resolution tier. R2V Flash only supports 720p and 1080p. Default value: `"1080p"`
  - Default: `"1080p"`
  - Options: `"720p"`, `"1080p"`

- **`duration`** (`DurationEnum`, _optional_):
  Duration of the generated video in seconds. R2V Flash supports only 5 or 10 seconds. Default value: `"5"`
  - Default: `"5"`
  - Options: `"5"`, `"10"`
  - Examples: "5", "10"

- **`negative_prompt`** (`string`, _optional_):
  Negative prompt to describe content to avoid. Max 500 characters. Default value: `""`
  - Default: `""`
  - Examples: "low resolution, error, worst quality, low quality, defects"

- **`enable_prompt_expansion`** (`boolean`, _optional_):
  Whether to enable prompt rewriting using LLM. Default value: `true`
  - Default: `true`

- **`multi_shots`** (`boolean`, _optional_):
  When true (default), enables intelligent multi-shot segmentation for coherent narrative videos with multiple shots. When false, generates single continuous shot. Only active when enable_prompt_expansion is True. Default value: `true`
  - Default: `true`

- **`generate_audio`** (`boolean`, _optional_):
  Whether to generate a video with audio. Set to false for silent video generation. Silent videos are faster and cost 25% of the audio version price. Default value: `true`
  - Default: `true`

- **`seed`** (`integer`, _optional_):
  Random seed for reproducibility. If None, a random seed is chosen.

- **`enable_safety_checker`** (`boolean`, _optional_):
  If set to true, the safety checker will be enabled. Default value: `true`
  - Default: `true`
  - Examples: true



**Required Parameters Example**:

```json
{
  "prompt": "Dance battle between Character1 and Character2."
}
```

**Full Example**:

```json
{
  "prompt": "Dance battle between Character1 and Character2.",
  "video_urls": [
    "https://v3b.fal.media/files/b/0a8d6d47/FtSBJGfZuivKfBIrRuWxa_video.mp4"
  ],
  "image_urls": [
    "https://v3b.fal.media/files/b/0a8d6d49/4XDgJcWQHLgkmUOL2JlPt_iXGPlm9y.png"
  ],
  "aspect_ratio": "16:9",
  "resolution": "1080p",
  "duration": "5",
  "negative_prompt": "low resolution, error, worst quality, low quality, defects",
  "enable_prompt_expansion": true,
  "multi_shots": true,
  "generate_audio": true,
  "enable_safety_checker": true
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`VideoFile`, _required_):
  The generated video file
  - Examples: {"url":"https://v3b.fal.media/files/b/0a86762b/iDknfPkLFSFwWkyMgJi0U_QIzjwBDQ.mp4","content_type":"video/mp4"}

- **`seed`** (`integer`, _required_):
  The seed used for generation
  - Examples: 175932751

- **`actual_prompt`** (`string`, _optional_):
  The actual prompt used if prompt rewriting was enabled
  - Examples: "Dance battle between Character1 and Character2, cinematic lighting, dynamic camera movement."



**Example Response**:

```json
{
  "video": {
    "url": "https://v3b.fal.media/files/b/0a86762b/iDknfPkLFSFwWkyMgJi0U_QIzjwBDQ.mp4",
    "content_type": "video/mp4"
  },
  "seed": 175932751,
  "actual_prompt": "Dance battle between Character1 and Character2, cinematic lighting, dynamic camera movement."
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/wan/v2.6/reference-to-video/flash \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "Dance battle between Character1 and Character2."
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
    "wan/v2.6/reference-to-video/flash",
    arguments={
        "prompt": "Dance battle between Character1 and Character2."
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

const result = await fal.subscribe("wan/v2.6/reference-to-video/flash", {
  input: {
    prompt: "Dance battle between Character1 and Character2."
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

- [Model Playground](https://fal.ai/models/wan/v2.6/reference-to-video/flash)
- [API Documentation](https://fal.ai/models/wan/v2.6/reference-to-video/flash/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=wan/v2.6/reference-to-video/flash)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
