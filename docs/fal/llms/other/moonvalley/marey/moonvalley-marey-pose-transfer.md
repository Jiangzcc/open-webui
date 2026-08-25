# Marey Realism V1.5

> Ideal for matching human movement. Your input video determines human poses, gestures, and body movements that will appear in the generated video.


## Overview

- **Endpoint**: `https://fal.run/moonvalley/marey/pose-transfer`
- **Model ID**: `moonvalley/marey/pose-transfer`
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
  - Examples: "Detailed Description: A venerable tribal chief, his weathered face marked with dark, ritualistic paint, stands proudly against a jungle backdrop. His elaborate headdress, a magnificent creation of numerous feathers, beads, and a central polished stone, sways gently with his movements. His initial stern expression softens into a confident smile as he begins to speak, his lips moving with unspoken words of wisdom or command. In a single, fluid motion, he raises his hand and gives a decisive wave, a gesture of both greeting and authority that underscores his leadership role within the tribe.\n\nBackground: A dense tropical rainforest is blurred into a soft, verdant backdrop, with muted greens and browns suggesting a lush, humid environment.\n\nMiddleground: The chief is the central focus, his head crowned by the large, intricate feathered headdress that moves subtly as he speaks. His shoulders and torso are visible, adorned with traditional necklaces.\n\nForeground: His hand lifts into the frame, palm open, executing a single, confident wave toward the viewer before lowering again. The closest feathers of his headdress rustle with the motion."

- **`video_url`** (`string`, _required_):
  The URL of the video to use as the control video.
  - Examples: "https://d1kaxrqq3vfrw5.cloudfront.net/fal-launch-assets/guide-assets/fal-pose-transfer-input.mp4"

- **`first_frame_image_url`** (`string`, _optional_):
  Optional first frame image URL to use as the first frame of the generated video

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
  "prompt": "Detailed Description: A venerable tribal chief, his weathered face marked with dark, ritualistic paint, stands proudly against a jungle backdrop. His elaborate headdress, a magnificent creation of numerous feathers, beads, and a central polished stone, sways gently with his movements. His initial stern expression softens into a confident smile as he begins to speak, his lips moving with unspoken words of wisdom or command. In a single, fluid motion, he raises his hand and gives a decisive wave, a gesture of both greeting and authority that underscores his leadership role within the tribe.\n\nBackground: A dense tropical rainforest is blurred into a soft, verdant backdrop, with muted greens and browns suggesting a lush, humid environment.\n\nMiddleground: The chief is the central focus, his head crowned by the large, intricate feathered headdress that moves subtly as he speaks. His shoulders and torso are visible, adorned with traditional necklaces.\n\nForeground: His hand lifts into the frame, palm open, executing a single, confident wave toward the viewer before lowering again. The closest feathers of his headdress rustle with the motion.",
  "video_url": "https://d1kaxrqq3vfrw5.cloudfront.net/fal-launch-assets/guide-assets/fal-pose-transfer-input.mp4"
}
```

**Full Example**:

```json
{
  "prompt": "Detailed Description: A venerable tribal chief, his weathered face marked with dark, ritualistic paint, stands proudly against a jungle backdrop. His elaborate headdress, a magnificent creation of numerous feathers, beads, and a central polished stone, sways gently with his movements. His initial stern expression softens into a confident smile as he begins to speak, his lips moving with unspoken words of wisdom or command. In a single, fluid motion, he raises his hand and gives a decisive wave, a gesture of both greeting and authority that underscores his leadership role within the tribe.\n\nBackground: A dense tropical rainforest is blurred into a soft, verdant backdrop, with muted greens and browns suggesting a lush, humid environment.\n\nMiddleground: The chief is the central focus, his head crowned by the large, intricate feathered headdress that moves subtly as he speaks. His shoulders and torso are visible, adorned with traditional necklaces.\n\nForeground: His hand lifts into the frame, palm open, executing a single, confident wave toward the viewer before lowering again. The closest feathers of his headdress rustle with the motion.",
  "video_url": "https://d1kaxrqq3vfrw5.cloudfront.net/fal-launch-assets/guide-assets/fal-pose-transfer-input.mp4",
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
  --url https://fal.run/moonvalley/marey/pose-transfer \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "Detailed Description: A venerable tribal chief, his weathered face marked with dark, ritualistic paint, stands proudly against a jungle backdrop. His elaborate headdress, a magnificent creation of numerous feathers, beads, and a central polished stone, sways gently with his movements. His initial stern expression softens into a confident smile as he begins to speak, his lips moving with unspoken words of wisdom or command. In a single, fluid motion, he raises his hand and gives a decisive wave, a gesture of both greeting and authority that underscores his leadership role within the tribe.\n\nBackground: A dense tropical rainforest is blurred into a soft, verdant backdrop, with muted greens and browns suggesting a lush, humid environment.\n\nMiddleground: The chief is the central focus, his head crowned by the large, intricate feathered headdress that moves subtly as he speaks. His shoulders and torso are visible, adorned with traditional necklaces.\n\nForeground: His hand lifts into the frame, palm open, executing a single, confident wave toward the viewer before lowering again. The closest feathers of his headdress rustle with the motion.",
     "video_url": "https://d1kaxrqq3vfrw5.cloudfront.net/fal-launch-assets/guide-assets/fal-pose-transfer-input.mp4"
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
    "moonvalley/marey/pose-transfer",
    arguments={
        "prompt": "Detailed Description: A venerable tribal chief, his weathered face marked with dark, ritualistic paint, stands proudly against a jungle backdrop. His elaborate headdress, a magnificent creation of numerous feathers, beads, and a central polished stone, sways gently with his movements. His initial stern expression softens into a confident smile as he begins to speak, his lips moving with unspoken words of wisdom or command. In a single, fluid motion, he raises his hand and gives a decisive wave, a gesture of both greeting and authority that underscores his leadership role within the tribe.

    Background: A dense tropical rainforest is blurred into a soft, verdant backdrop, with muted greens and browns suggesting a lush, humid environment.

    Middleground: The chief is the central focus, his head crowned by the large, intricate feathered headdress that moves subtly as he speaks. His shoulders and torso are visible, adorned with traditional necklaces.

    Foreground: His hand lifts into the frame, palm open, executing a single, confident wave toward the viewer before lowering again. The closest feathers of his headdress rustle with the motion.",
        "video_url": "https://d1kaxrqq3vfrw5.cloudfront.net/fal-launch-assets/guide-assets/fal-pose-transfer-input.mp4"
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

const result = await fal.subscribe("moonvalley/marey/pose-transfer", {
  input: {
    prompt: "Detailed Description: A venerable tribal chief, his weathered face marked with dark, ritualistic paint, stands proudly against a jungle backdrop. His elaborate headdress, a magnificent creation of numerous feathers, beads, and a central polished stone, sways gently with his movements. His initial stern expression softens into a confident smile as he begins to speak, his lips moving with unspoken words of wisdom or command. In a single, fluid motion, he raises his hand and gives a decisive wave, a gesture of both greeting and authority that underscores his leadership role within the tribe.

  Background: A dense tropical rainforest is blurred into a soft, verdant backdrop, with muted greens and browns suggesting a lush, humid environment.

  Middleground: The chief is the central focus, his head crowned by the large, intricate feathered headdress that moves subtly as he speaks. His shoulders and torso are visible, adorned with traditional necklaces.

  Foreground: His hand lifts into the frame, palm open, executing a single, confident wave toward the viewer before lowering again. The closest feathers of his headdress rustle with the motion.",
    video_url: "https://d1kaxrqq3vfrw5.cloudfront.net/fal-launch-assets/guide-assets/fal-pose-transfer-input.mp4"
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

- [Model Playground](https://fal.ai/models/moonvalley/marey/pose-transfer)
- [API Documentation](https://fal.ai/models/moonvalley/marey/pose-transfer/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=moonvalley/marey/pose-transfer)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
