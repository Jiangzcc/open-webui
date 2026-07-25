# Imagineart 2.0 Preview

> ImagineArt 2.0 is ImagineArt's latest state-of-the-art visual reasoning text-to-image model, generating high-fidelity, professional-grade visuals with lifelike realism, cinematic effects, and strong aesthetic quality.


## Overview

- **Endpoint**: `https://fal.run/imagineart/imagineart-2.0-preview/text-to-image`
- **Model ID**: `imagineart/imagineart-2.0-preview/text-to-image`
- **Category**: text-to-image
- **Kind**: inference
**Tags**: stylized, transform, typography



## Pricing

Your request will cost 1K at **$0.03** and 2K at **$0.05** per image generation.

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _required_):
  Text prompt describing the desired image
  - Examples: "Photorealistic cinematic portrait of a stressed young woman with dark skin and long brown dreadlocks styled in a messy high bun, wearing black-rimmed glasses and a peach-colored collared shirt. She is sitting at a desk, sipping coffee from a white ceramic mug held in her right hand, with a focused and slightly overwhelmed expression while looking at a silver laptop in front of her.\n\nHer face, hair, glasses, and entire upper body are completely covered with dozens of colorful sticky notes in yellow, pink, blue, orange, red, and green, many with no written text. Sticky notes are stuck to her forehead, cheeks, dreadlocks, and all over her shirt.\n\nThe scene is set in a modern office with soft cool blue-toned natural lighting coming from the side. Blurred green plants are visible in the background and \"ImagineArt\" is written on the Wall. On the desk in the foreground there is another white mug, scattered papers, and more sticky notes.\n\nHighly detailed, sharp focus on the woman, shallow depth of field, realistic skin texture, natural fabric folds, cinematic lighting, moody atmosphere capturing information overload and multitasking, 8k resolution, photorealistic."

- **`aspect_ratio`** (`AspectRatioEnum`, _optional_):
  Image aspect ratio: 1:1, 3:1, 1:3, 16:9, 9:16, 4:3, 3:4, 3:2, 2:3, 21:9, 4:5, 5:4, 4:1, 1:4 Default value: `"1:1"`
  - Default: `"1:1"`
  - Options: `"1:1"`, `"16:9"`, `"9:16"`, `"4:3"`, `"3:4"`, `"3:1"`, `"1:3"`, `"3:2"`, `"2:3"`, `"21:9"`, `"4:5"`, `"5:4"`, `"4:1"`, `"1:4"`
  - Examples: "1:1"

- **`resolution`** (`ResolutionEnum`, _optional_):
  Output resolution: '1K' targets ~1024px and will be faster. '2K' targets ~2048px image size and will be slower but with higher quality. Default value: `"2K"`
  - Default: `"2K"`
  - Options: `"1K"`, `"2K"`
  - Examples: "2K"

- **`seed`** (`integer`, _optional_):
  Default is random (0 and -1 are treated as random)
  - Examples: 0

- **`reasoning`** (`ReasoningEnum`, _optional_):
  Visual Understanding Level: low (default) or high. High reasoning takes more time but generates better images. Default value: `"low"`
  - Default: `"low"`
  - Options: `"high"`, `"low"`
  - Examples: "low"



**Required Parameters Example**:

```json
{
  "prompt": "Photorealistic cinematic portrait of a stressed young woman with dark skin and long brown dreadlocks styled in a messy high bun, wearing black-rimmed glasses and a peach-colored collared shirt. She is sitting at a desk, sipping coffee from a white ceramic mug held in her right hand, with a focused and slightly overwhelmed expression while looking at a silver laptop in front of her.\n\nHer face, hair, glasses, and entire upper body are completely covered with dozens of colorful sticky notes in yellow, pink, blue, orange, red, and green, many with no written text. Sticky notes are stuck to her forehead, cheeks, dreadlocks, and all over her shirt.\n\nThe scene is set in a modern office with soft cool blue-toned natural lighting coming from the side. Blurred green plants are visible in the background and \"ImagineArt\" is written on the Wall. On the desk in the foreground there is another white mug, scattered papers, and more sticky notes.\n\nHighly detailed, sharp focus on the woman, shallow depth of field, realistic skin texture, natural fabric folds, cinematic lighting, moody atmosphere capturing information overload and multitasking, 8k resolution, photorealistic."
}
```

**Full Example**:

```json
{
  "prompt": "Photorealistic cinematic portrait of a stressed young woman with dark skin and long brown dreadlocks styled in a messy high bun, wearing black-rimmed glasses and a peach-colored collared shirt. She is sitting at a desk, sipping coffee from a white ceramic mug held in her right hand, with a focused and slightly overwhelmed expression while looking at a silver laptop in front of her.\n\nHer face, hair, glasses, and entire upper body are completely covered with dozens of colorful sticky notes in yellow, pink, blue, orange, red, and green, many with no written text. Sticky notes are stuck to her forehead, cheeks, dreadlocks, and all over her shirt.\n\nThe scene is set in a modern office with soft cool blue-toned natural lighting coming from the side. Blurred green plants are visible in the background and \"ImagineArt\" is written on the Wall. On the desk in the foreground there is another white mug, scattered papers, and more sticky notes.\n\nHighly detailed, sharp focus on the woman, shallow depth of field, realistic skin texture, natural fabric folds, cinematic lighting, moody atmosphere capturing information overload and multitasking, 8k resolution, photorealistic.",
  "aspect_ratio": "1:1",
  "resolution": "2K",
  "seed": 0,
  "reasoning": "low"
}
```


### Output Schema

The API returns the following output format:

- **`images`** (`list<Image>`, _required_):
  Generated image
  - Array of Image
  - Examples: [{"url":"https://v3b.fal.media/files/b/0a9513b1/to-rcKHMkC7e9jQFN7tZE_U8VLyc50wRU6V_UbIh0Hi_generated_ImagineArt_2_0.png","width":2048,"content_type":"image/png","height":2048}]



**Example Response**:

```json
{
  "images": [
    {
      "url": "https://v3b.fal.media/files/b/0a9513b1/to-rcKHMkC7e9jQFN7tZE_U8VLyc50wRU6V_UbIh0Hi_generated_ImagineArt_2_0.png",
      "width": 2048,
      "content_type": "image/png",
      "height": 2048
    }
  ]
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/imagineart/imagineart-2.0-preview/text-to-image \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "Photorealistic cinematic portrait of a stressed young woman with dark skin and long brown dreadlocks styled in a messy high bun, wearing black-rimmed glasses and a peach-colored collared shirt. She is sitting at a desk, sipping coffee from a white ceramic mug held in her right hand, with a focused and slightly overwhelmed expression while looking at a silver laptop in front of her.\n\nHer face, hair, glasses, and entire upper body are completely covered with dozens of colorful sticky notes in yellow, pink, blue, orange, red, and green, many with no written text. Sticky notes are stuck to her forehead, cheeks, dreadlocks, and all over her shirt.\n\nThe scene is set in a modern office with soft cool blue-toned natural lighting coming from the side. Blurred green plants are visible in the background and \"ImagineArt\" is written on the Wall. On the desk in the foreground there is another white mug, scattered papers, and more sticky notes.\n\nHighly detailed, sharp focus on the woman, shallow depth of field, realistic skin texture, natural fabric folds, cinematic lighting, moody atmosphere capturing information overload and multitasking, 8k resolution, photorealistic."
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
    "imagineart/imagineart-2.0-preview/text-to-image",
    arguments={
        "prompt": "Photorealistic cinematic portrait of a stressed young woman with dark skin and long brown dreadlocks styled in a messy high bun, wearing black-rimmed glasses and a peach-colored collared shirt. She is sitting at a desk, sipping coffee from a white ceramic mug held in her right hand, with a focused and slightly overwhelmed expression while looking at a silver laptop in front of her.

    Her face, hair, glasses, and entire upper body are completely covered with dozens of colorful sticky notes in yellow, pink, blue, orange, red, and green, many with no written text. Sticky notes are stuck to her forehead, cheeks, dreadlocks, and all over her shirt.

    The scene is set in a modern office with soft cool blue-toned natural lighting coming from the side. Blurred green plants are visible in the background and \"ImagineArt\" is written on the Wall. On the desk in the foreground there is another white mug, scattered papers, and more sticky notes.

    Highly detailed, sharp focus on the woman, shallow depth of field, realistic skin texture, natural fabric folds, cinematic lighting, moody atmosphere capturing information overload and multitasking, 8k resolution, photorealistic."
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

const result = await fal.subscribe("imagineart/imagineart-2.0-preview/text-to-image", {
  input: {
    prompt: "Photorealistic cinematic portrait of a stressed young woman with dark skin and long brown dreadlocks styled in a messy high bun, wearing black-rimmed glasses and a peach-colored collared shirt. She is sitting at a desk, sipping coffee from a white ceramic mug held in her right hand, with a focused and slightly overwhelmed expression while looking at a silver laptop in front of her.

  Her face, hair, glasses, and entire upper body are completely covered with dozens of colorful sticky notes in yellow, pink, blue, orange, red, and green, many with no written text. Sticky notes are stuck to her forehead, cheeks, dreadlocks, and all over her shirt.

  The scene is set in a modern office with soft cool blue-toned natural lighting coming from the side. Blurred green plants are visible in the background and \"ImagineArt\" is written on the Wall. On the desk in the foreground there is another white mug, scattered papers, and more sticky notes.

  Highly detailed, sharp focus on the woman, shallow depth of field, realistic skin texture, natural fabric folds, cinematic lighting, moody atmosphere capturing information overload and multitasking, 8k resolution, photorealistic."
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

- [Model Playground](https://fal.ai/models/imagineart/imagineart-2.0-preview/text-to-image)
- [API Documentation](https://fal.ai/models/imagineart/imagineart-2.0-preview/text-to-image/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=imagineart/imagineart-2.0-preview/text-to-image)

### fal.ai Platform

- [Platform Documentation](https://docs.fal.ai)
- [Python Client](https://docs.fal.ai/clients/python)
- [JavaScript Client](https://docs.fal.ai/clients/javascript)
