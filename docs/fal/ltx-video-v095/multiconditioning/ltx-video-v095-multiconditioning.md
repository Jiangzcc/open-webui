# LTX Video-0.9.5

> Generate videos from prompts,images, and videos using LTX Video-0.9.5


## Overview

- **Endpoint**: `https://fal.run/fal-ai/ltx-video-v095/multiconditioning`
- **Model ID**: `fal-ai/ltx-video-v095/multiconditioning`
- **Category**: video-to-video
- **Kind**: inference
**Tags**: video, image-to-video, text-to-video



## Pricing

- **Price**: $0.04 per videos

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _required_):
  Text prompt to guide generation
  - Examples: "\n            A vibrant, abstract composition featuring a person with outstretched arms, rendered in a kaleidoscope of colors against a deep, dark background. The figure is composed of intricate, swirling patterns reminiscent of a mosaic, with hues of orange, yellow, blue, and green that evoke the style of artists such as Wassily Kandinsky or Bridget Riley. \n\nThe camera zooms into the face striking portrait of a man, reimagined through the lens of old-school video-game graphics. The subject's face is rendered in a kaleidoscope of colors, with bold blues and reds set against a vibrant yellow backdrop. His dark hair is pulled back, framing his profile in a dramatic pose\n        "

- **`negative_prompt`** (`string`, _optional_):
  Negative prompt for generation Default value: `"worst quality, inconsistent motion, blurry, jittery, distorted"`
  - Default: `"worst quality, inconsistent motion, blurry, jittery, distorted"`

- **`resolution`** (`ResolutionEnum`, _optional_):
  Resolution of the generated video (480p or 720p). Default value: `"720p"`
  - Default: `"720p"`
  - Options: `"480p"`, `"720p"`

- **`aspect_ratio`** (`AspectRatioEnum`, _optional_):
  Aspect ratio of the generated video (16:9 or 9:16). Default value: `"16:9"`
  - Default: `"16:9"`
  - Options: `"9:16"`, `"16:9"`

- **`seed`** (`integer`, _optional_):
  Random seed for generation

- **`num_inference_steps`** (`integer`, _optional_):
  Number of inference steps Default value: `40`
  - Default: `40`
  - Range: `2` to `50`

- **`expand_prompt`** (`boolean`, _optional_):
  Whether to expand the prompt using the model's own capabilities. Default value: `true`
  - Default: `true`

- **`images`** (`list<ImageConditioningInput>`, _optional_):
  URL of images to use as conditioning
  - Default: `[]`
  - Array of ImageConditioningInput
  - Examples: [{"start_frame_num":0,"image_url":"https://storage.googleapis.com/falserverless/model_tests/ltx/NswO1P8sCLzrh1WefqQFK_9a6bdbfa54b944c9a770338159a113fd.jpg"},{"start_frame_num":120,"image_url":"https://storage.googleapis.com/falserverless/model_tests/ltx/YAPOGvmS2tM_Krdp7q6-d_267c97e017c34f679844a4477dfcec38.jpg"}]

- **`videos`** (`list<VideoConditioningInput>`, _optional_):
  Videos to use as conditioning
  - Default: `[]`
  - Array of VideoConditioningInput



**Required Parameters Example**:

```json
{
  "prompt": "\n            A vibrant, abstract composition featuring a person with outstretched arms, rendered in a kaleidoscope of colors against a deep, dark background. The figure is composed of intricate, swirling patterns reminiscent of a mosaic, with hues of orange, yellow, blue, and green that evoke the style of artists such as Wassily Kandinsky or Bridget Riley. \n\nThe camera zooms into the face striking portrait of a man, reimagined through the lens of old-school video-game graphics. The subject's face is rendered in a kaleidoscope of colors, with bold blues and reds set against a vibrant yellow backdrop. His dark hair is pulled back, framing his profile in a dramatic pose\n        "
}
```

**Full Example**:

```json
{
  "prompt": "\n            A vibrant, abstract composition featuring a person with outstretched arms, rendered in a kaleidoscope of colors against a deep, dark background. The figure is composed of intricate, swirling patterns reminiscent of a mosaic, with hues of orange, yellow, blue, and green that evoke the style of artists such as Wassily Kandinsky or Bridget Riley. \n\nThe camera zooms into the face striking portrait of a man, reimagined through the lens of old-school video-game graphics. The subject's face is rendered in a kaleidoscope of colors, with bold blues and reds set against a vibrant yellow backdrop. His dark hair is pulled back, framing his profile in a dramatic pose\n        ",
  "negative_prompt": "worst quality, inconsistent motion, blurry, jittery, distorted",
  "resolution": "720p",
  "aspect_ratio": "16:9",
  "num_inference_steps": 40,
  "expand_prompt": true,
  "images": [
    {
      "start_frame_num": 0,
      "image_url": "https://storage.googleapis.com/falserverless/model_tests/ltx/NswO1P8sCLzrh1WefqQFK_9a6bdbfa54b944c9a770338159a113fd.jpg"
    },
    {
      "start_frame_num": 120,
      "image_url": "https://storage.googleapis.com/falserverless/model_tests/ltx/YAPOGvmS2tM_Krdp7q6-d_267c97e017c34f679844a4477dfcec38.jpg"
    }
  ],
  "videos": []
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`File`, _required_):
  The generated video file.
  - Examples: {"url":"https://storage.googleapis.com/falserverless/gallery/ltx-multicondition.mp4"}

- **`seed`** (`integer`, _required_):
  The seed used for generation.



**Example Response**:

```json
{
  "video": {
    "url": "https://storage.googleapis.com/falserverless/gallery/ltx-multicondition.mp4"
  }
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/ltx-video-v095/multiconditioning \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "\n            A vibrant, abstract composition featuring a person with outstretched arms, rendered in a kaleidoscope of colors against a deep, dark background. The figure is composed of intricate, swirling patterns reminiscent of a mosaic, with hues of orange, yellow, blue, and green that evoke the style of artists such as Wassily Kandinsky or Bridget Riley. \n\nThe camera zooms into the face striking portrait of a man, reimagined through the lens of old-school video-game graphics. The subject's face is rendered in a kaleidoscope of colors, with bold blues and reds set against a vibrant yellow backdrop. His dark hair is pulled back, framing his profile in a dramatic pose\n        "
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
    "fal-ai/ltx-video-v095/multiconditioning",
    arguments={
        "prompt": "
                A vibrant, abstract composition featuring a person with outstretched arms, rendered in a kaleidoscope of colors against a deep, dark background. The figure is composed of intricate, swirling patterns reminiscent of a mosaic, with hues of orange, yellow, blue, and green that evoke the style of artists such as Wassily Kandinsky or Bridget Riley.

    The camera zooms into the face striking portrait of a man, reimagined through the lens of old-school video-game graphics. The subject's face is rendered in a kaleidoscope of colors, with bold blues and reds set against a vibrant yellow backdrop. His dark hair is pulled back, framing his profile in a dramatic pose
            "
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

const result = await fal.subscribe("fal-ai/ltx-video-v095/multiconditioning", {
  input: {
    prompt: "
              A vibrant, abstract composition featuring a person with outstretched arms, rendered in a kaleidoscope of colors against a deep, dark background. The figure is composed of intricate, swirling patterns reminiscent of a mosaic, with hues of orange, yellow, blue, and green that evoke the style of artists such as Wassily Kandinsky or Bridget Riley.

  The camera zooms into the face striking portrait of a man, reimagined through the lens of old-school video-game graphics. The subject's face is rendered in a kaleidoscope of colors, with bold blues and reds set against a vibrant yellow backdrop. His dark hair is pulled back, framing his profile in a dramatic pose
          "
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

- [Model Playground](https://fal.ai/models/fal-ai/ltx-video-v095/multiconditioning)
- [API Documentation](https://fal.ai/models/fal-ai/ltx-video-v095/multiconditioning/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/ltx-video-v095/multiconditioning)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
