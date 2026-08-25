# Marey Realism V1.5

> Pull motion from a reference video and apply it to new subjects or scenes.


## Overview

- **Endpoint**: `https://fal.run/moonvalley/marey/motion-transfer`
- **Model ID**: `moonvalley/marey/motion-transfer`
- **Category**: video-to-video
- **Kind**: inference


## Pricing

Your request will cost **$2.00** per video.

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _required_):
  The prompt to generate a video from
  - Examples: "Detailed Description: A fast, smooth dolly shot glides forward at water level through a monumental, minimalist colonnade. The imposing, symmetrical rows of brutalist marble columns rush past on either side, their strong vertical lines creating a sense of powerful, constant motion. The dark, glassy water of a central pool perfectly reflects the towering structures, with gentle ripples disturbing the mirror image as the camera advances. The scene is cinematic and moody, with the light-colored stone contrasting against the dark water and the pale sky visible at the far end of the architectural tunnel. shot on 35mm, film, organic, analog, motion blur\n\nBackground: A pale, overcast sky and a distant treeline are framed by the opening at the end of the colonnade, growing larger as the camera moves forward.\n\nMiddleground: The two rows of massive, geometric columns recede into the distance, their uniform shapes creating a hypnotic, rhythmic pattern that rushes past the lens.\n\nForeground: The camera skims just above the surface of the dark, rippling water, which reflects the blurred motion of the columns passing on the left and right."

- **`video_url`** (`string`, _required_):
  The URL of the video to use as the control video.
  - Examples: "https://d1kaxrqq3vfrw5.cloudfront.net/fal-launch-assets/guide-assets/fal-motion-transfer-input-5s.mp4"

- **`first_frame_image_url`** (`string`, _optional_):
  Optional first frame image URL to use as the first frame of the generated video Default value: `"https://video-editor-files-prod.s3.us-east-2.amazonaws.com/users/1e4d46df-0702-4491-95ce-763592f33f34/uploaded-images/9b9dce1c-abd0-46c0-bac9-9454f8893b06/original"`
  - Default: `"https://video-editor-files-prod.s3.us-east-2.amazonaws.com/users/1e4d46df-0702-4491-95ce-763592f33f34/uploaded-images/9b9dce1c-abd0-46c0-bac9-9454f8893b06/original"`

- **`reference_image_url`** (`string`, _optional_):
  Optional reference image URL to use for pose control or as a starting frame

- **`negative_prompt`** (`string`, _optional_):
  Negative prompt used to guide the model away from undesirable features. Default value: `"<synthetic> <scene cut> low-poly, flat shader, bad rigging, stiff animation, uncanny eyes, low-quality textures, looping glitch, cheap effect, overbloom, bloom spam, default lighting, game asset, stiff face, ugly specular, AI artifacts"`
  - Default: `"<synthetic> <scene cut> low-poly, flat shader, bad rigging, stiff animation, uncanny eyes, low-quality textures, looping glitch, cheap effect, overbloom, bloom spam, default lighting, game asset, stiff face, ugly specular, AI artifacts"`

- **`seed`** (`integer`, _optional_):
  Seed for random number generation. Use -1 for random seed each run. Default value: `-1`
  - Default: `-1`



**Required Parameters Example**:

```json
{
  "prompt": "Detailed Description: A fast, smooth dolly shot glides forward at water level through a monumental, minimalist colonnade. The imposing, symmetrical rows of brutalist marble columns rush past on either side, their strong vertical lines creating a sense of powerful, constant motion. The dark, glassy water of a central pool perfectly reflects the towering structures, with gentle ripples disturbing the mirror image as the camera advances. The scene is cinematic and moody, with the light-colored stone contrasting against the dark water and the pale sky visible at the far end of the architectural tunnel. shot on 35mm, film, organic, analog, motion blur\n\nBackground: A pale, overcast sky and a distant treeline are framed by the opening at the end of the colonnade, growing larger as the camera moves forward.\n\nMiddleground: The two rows of massive, geometric columns recede into the distance, their uniform shapes creating a hypnotic, rhythmic pattern that rushes past the lens.\n\nForeground: The camera skims just above the surface of the dark, rippling water, which reflects the blurred motion of the columns passing on the left and right.",
  "video_url": "https://d1kaxrqq3vfrw5.cloudfront.net/fal-launch-assets/guide-assets/fal-motion-transfer-input-5s.mp4"
}
```

**Full Example**:

```json
{
  "prompt": "Detailed Description: A fast, smooth dolly shot glides forward at water level through a monumental, minimalist colonnade. The imposing, symmetrical rows of brutalist marble columns rush past on either side, their strong vertical lines creating a sense of powerful, constant motion. The dark, glassy water of a central pool perfectly reflects the towering structures, with gentle ripples disturbing the mirror image as the camera advances. The scene is cinematic and moody, with the light-colored stone contrasting against the dark water and the pale sky visible at the far end of the architectural tunnel. shot on 35mm, film, organic, analog, motion blur\n\nBackground: A pale, overcast sky and a distant treeline are framed by the opening at the end of the colonnade, growing larger as the camera moves forward.\n\nMiddleground: The two rows of massive, geometric columns recede into the distance, their uniform shapes creating a hypnotic, rhythmic pattern that rushes past the lens.\n\nForeground: The camera skims just above the surface of the dark, rippling water, which reflects the blurred motion of the columns passing on the left and right.",
  "video_url": "https://d1kaxrqq3vfrw5.cloudfront.net/fal-launch-assets/guide-assets/fal-motion-transfer-input-5s.mp4",
  "first_frame_image_url": "https://video-editor-files-prod.s3.us-east-2.amazonaws.com/users/1e4d46df-0702-4491-95ce-763592f33f34/uploaded-images/9b9dce1c-abd0-46c0-bac9-9454f8893b06/original",
  "negative_prompt": "<synthetic> <scene cut> low-poly, flat shader, bad rigging, stiff animation, uncanny eyes, low-quality textures, looping glitch, cheap effect, overbloom, bloom spam, default lighting, game asset, stiff face, ugly specular, AI artifacts",
  "seed": -1
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`File`, _required_):
  The generated video.



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
  --url https://fal.run/moonvalley/marey/motion-transfer \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "Detailed Description: A fast, smooth dolly shot glides forward at water level through a monumental, minimalist colonnade. The imposing, symmetrical rows of brutalist marble columns rush past on either side, their strong vertical lines creating a sense of powerful, constant motion. The dark, glassy water of a central pool perfectly reflects the towering structures, with gentle ripples disturbing the mirror image as the camera advances. The scene is cinematic and moody, with the light-colored stone contrasting against the dark water and the pale sky visible at the far end of the architectural tunnel. shot on 35mm, film, organic, analog, motion blur\n\nBackground: A pale, overcast sky and a distant treeline are framed by the opening at the end of the colonnade, growing larger as the camera moves forward.\n\nMiddleground: The two rows of massive, geometric columns recede into the distance, their uniform shapes creating a hypnotic, rhythmic pattern that rushes past the lens.\n\nForeground: The camera skims just above the surface of the dark, rippling water, which reflects the blurred motion of the columns passing on the left and right.",
     "video_url": "https://d1kaxrqq3vfrw5.cloudfront.net/fal-launch-assets/guide-assets/fal-motion-transfer-input-5s.mp4"
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
    "moonvalley/marey/motion-transfer",
    arguments={
        "prompt": "Detailed Description: A fast, smooth dolly shot glides forward at water level through a monumental, minimalist colonnade. The imposing, symmetrical rows of brutalist marble columns rush past on either side, their strong vertical lines creating a sense of powerful, constant motion. The dark, glassy water of a central pool perfectly reflects the towering structures, with gentle ripples disturbing the mirror image as the camera advances. The scene is cinematic and moody, with the light-colored stone contrasting against the dark water and the pale sky visible at the far end of the architectural tunnel. shot on 35mm, film, organic, analog, motion blur

    Background: A pale, overcast sky and a distant treeline are framed by the opening at the end of the colonnade, growing larger as the camera moves forward.

    Middleground: The two rows of massive, geometric columns recede into the distance, their uniform shapes creating a hypnotic, rhythmic pattern that rushes past the lens.

    Foreground: The camera skims just above the surface of the dark, rippling water, which reflects the blurred motion of the columns passing on the left and right.",
        "video_url": "https://d1kaxrqq3vfrw5.cloudfront.net/fal-launch-assets/guide-assets/fal-motion-transfer-input-5s.mp4"
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

const result = await fal.subscribe("moonvalley/marey/motion-transfer", {
  input: {
    prompt: "Detailed Description: A fast, smooth dolly shot glides forward at water level through a monumental, minimalist colonnade. The imposing, symmetrical rows of brutalist marble columns rush past on either side, their strong vertical lines creating a sense of powerful, constant motion. The dark, glassy water of a central pool perfectly reflects the towering structures, with gentle ripples disturbing the mirror image as the camera advances. The scene is cinematic and moody, with the light-colored stone contrasting against the dark water and the pale sky visible at the far end of the architectural tunnel. shot on 35mm, film, organic, analog, motion blur

  Background: A pale, overcast sky and a distant treeline are framed by the opening at the end of the colonnade, growing larger as the camera moves forward.

  Middleground: The two rows of massive, geometric columns recede into the distance, their uniform shapes creating a hypnotic, rhythmic pattern that rushes past the lens.

  Foreground: The camera skims just above the surface of the dark, rippling water, which reflects the blurred motion of the columns passing on the left and right.",
    video_url: "https://d1kaxrqq3vfrw5.cloudfront.net/fal-launch-assets/guide-assets/fal-motion-transfer-input-5s.mp4"
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

- [Model Playground](https://fal.ai/models/moonvalley/marey/motion-transfer)
- [API Documentation](https://fal.ai/models/moonvalley/marey/motion-transfer/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=moonvalley/marey/motion-transfer)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
