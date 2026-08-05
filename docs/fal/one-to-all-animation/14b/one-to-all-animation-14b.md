# One To All Animation

> One-to-All Animation is a pose driven video model that animates characters from a single reference image, enabling flexible, alignment-free motion transfer across diverse styles and scenes


## Overview

- **Endpoint**: `https://fal.run/fal-ai/one-to-all-animation/14b`
- **Model ID**: `fal-ai/one-to-all-animation/14b`
- **Category**: video-to-video
- **Kind**: inference
**Tags**: video to video, motion



## Pricing

Your request will cost **$0.12** per **video second** for **720p**, **$0.09** per **video second** for **580p**, **$0.06** per **video second** for **480p**.

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _required_):
  The prompt to generate the video from.
  - Examples: "A robot figure dancing"

- **`negative_prompt`** (`string`, _required_):
  The negative prompt to generate the video from.
  - Examples: "black background, Aerial view, aerial view, overexposed, low quality, deformation, a poor composition, bad hands, bad teeth, bad eyes, bad limbs, distortion"

- **`image_url`** (`string`, _required_):
  The URL of the image to use as a reference for the video generation.
  - Examples: "https://v3b.fal.media/files/b/panda/-oMlZo9Yyj_Nzoza_tgds_GmLF86r5bOt50eMMKCszy_eacc949b3933443c9915a83c98fbe85e.png"

- **`video_url`** (`string`, _required_):
  The URL of the video to use as a reference for the video generation.
  - Examples: "https://v3b.fal.media/files/b/panda/a6SvJg96V8eoglMlYFShU_5385885-hd_1080_1920_25fps.mp4"

- **`resolution`** (`ResolutionEnum`, _optional_):
  The resolution of the video to generate. Default value: `"480p"`
  - Default: `"480p"`
  - Options: `"480p"`, `"580p"`, `"720p"`

- **`num_inference_steps`** (`integer`, _optional_):
  The number of inference steps to use for the video generation. Default value: `30`
  - Default: `30`
  - Range: `2` to `30`

- **`image_guidance_scale`** (`float`, _optional_):
  The image guidance scale to use for the video generation. Default value: `2`
  - Default: `2`
  - Range: `1` to `10`

- **`pose_guidance_scale`** (`float`, _optional_):
  The pose guidance scale to use for the video generation. Default value: `1.5`
  - Default: `1.5`
  - Range: `1` to `10`



**Required Parameters Example**:

```json
{
  "prompt": "A robot figure dancing",
  "negative_prompt": "black background, Aerial view, aerial view, overexposed, low quality, deformation, a poor composition, bad hands, bad teeth, bad eyes, bad limbs, distortion",
  "image_url": "https://v3b.fal.media/files/b/panda/-oMlZo9Yyj_Nzoza_tgds_GmLF86r5bOt50eMMKCszy_eacc949b3933443c9915a83c98fbe85e.png",
  "video_url": "https://v3b.fal.media/files/b/panda/a6SvJg96V8eoglMlYFShU_5385885-hd_1080_1920_25fps.mp4"
}
```

**Full Example**:

```json
{
  "prompt": "A robot figure dancing",
  "negative_prompt": "black background, Aerial view, aerial view, overexposed, low quality, deformation, a poor composition, bad hands, bad teeth, bad eyes, bad limbs, distortion",
  "image_url": "https://v3b.fal.media/files/b/panda/-oMlZo9Yyj_Nzoza_tgds_GmLF86r5bOt50eMMKCszy_eacc949b3933443c9915a83c98fbe85e.png",
  "video_url": "https://v3b.fal.media/files/b/panda/a6SvJg96V8eoglMlYFShU_5385885-hd_1080_1920_25fps.mp4",
  "resolution": "480p",
  "num_inference_steps": 30,
  "image_guidance_scale": 2,
  "pose_guidance_scale": 1.5
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`File`, _required_):
  The generated video file.
  - Examples: {"file_name":"output.mp4","file_size":225893,"content_type":"application/octet-stream","url":"https://v3b.fal.media/files/b/0a85e79d/KOuXylETzdzUzMFFWLa4h_output.mp4"}



**Example Response**:

```json
{
  "video": {
    "file_name": "output.mp4",
    "file_size": 225893,
    "content_type": "application/octet-stream",
    "url": "https://v3b.fal.media/files/b/0a85e79d/KOuXylETzdzUzMFFWLa4h_output.mp4"
  }
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/one-to-all-animation/14b \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "A robot figure dancing",
     "negative_prompt": "black background, Aerial view, aerial view, overexposed, low quality, deformation, a poor composition, bad hands, bad teeth, bad eyes, bad limbs, distortion",
     "image_url": "https://v3b.fal.media/files/b/panda/-oMlZo9Yyj_Nzoza_tgds_GmLF86r5bOt50eMMKCszy_eacc949b3933443c9915a83c98fbe85e.png",
     "video_url": "https://v3b.fal.media/files/b/panda/a6SvJg96V8eoglMlYFShU_5385885-hd_1080_1920_25fps.mp4"
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
    "fal-ai/one-to-all-animation/14b",
    arguments={
        "prompt": "A robot figure dancing",
        "negative_prompt": "black background, Aerial view, aerial view, overexposed, low quality, deformation, a poor composition, bad hands, bad teeth, bad eyes, bad limbs, distortion",
        "image_url": "https://v3b.fal.media/files/b/panda/-oMlZo9Yyj_Nzoza_tgds_GmLF86r5bOt50eMMKCszy_eacc949b3933443c9915a83c98fbe85e.png",
        "video_url": "https://v3b.fal.media/files/b/panda/a6SvJg96V8eoglMlYFShU_5385885-hd_1080_1920_25fps.mp4"
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

const result = await fal.subscribe("fal-ai/one-to-all-animation/14b", {
  input: {
    prompt: "A robot figure dancing",
    negative_prompt: "black background, Aerial view, aerial view, overexposed, low quality, deformation, a poor composition, bad hands, bad teeth, bad eyes, bad limbs, distortion",
    image_url: "https://v3b.fal.media/files/b/panda/-oMlZo9Yyj_Nzoza_tgds_GmLF86r5bOt50eMMKCszy_eacc949b3933443c9915a83c98fbe85e.png",
    video_url: "https://v3b.fal.media/files/b/panda/a6SvJg96V8eoglMlYFShU_5385885-hd_1080_1920_25fps.mp4"
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

- [Model Playground](https://fal.ai/models/fal-ai/one-to-all-animation/14b)
- [API Documentation](https://fal.ai/models/fal-ai/one-to-all-animation/14b/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/one-to-all-animation/14b)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
