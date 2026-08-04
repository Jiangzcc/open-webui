# ImagineArt 1.5 Pro Preview

> ImagineArt 1.5 Pro is an advanced text-to-image model that creates ultra-high-fidelity 4K visuals with lifelike realism, refined aesthetics, and powerful creative output suited for professional use.


## Overview

- **Endpoint**: `https://fal.run/imagineart/imagineart-1.5-pro-preview/text-to-image`
- **Model ID**: `imagineart/imagineart-1.5-pro-preview/text-to-image`
- **Category**: text-to-image
- **Kind**: inference
**Tags**: visuals, imagineart, realism, text



## Pricing

- **Price**: $0.045 per images

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _required_):
  Text prompt describing the desired image. Accepts either a raw string or a JSON string/fenced JSON with positive_prompt and optional negative_prompt.
  - Examples: "Photorealistic cinematic portrait of a stressed young woman with dark skin and long brown dreadlocks styled in a messy high bun, wearing black-rimmed glasses and a peach-colored collared shirt. She is sitting at a desk, sipping coffee from a white ceramic mug held in her right hand, with a focused and slightly overwhelmed expression while looking at a silver laptop in front of her.\n\nHer face, hair, glasses, and entire upper body are completely covered with dozens of colorful sticky notes in yellow, pink, blue, orange, red, and green, many with no written text. Sticky notes are stuck to her forehead, cheeks, dreadlocks, and all over her shirt.\n\nThe scene is set in a modern office with soft cool blue-toned natural lighting coming from the side. Blurred green plants are visible in the background and \"ImagineArt\" is written on the Wall. On the desk in the foreground there is another white mug, scattered papers, and more sticky notes.\n\nHighly detailed, sharp focus on the woman, shallow depth of field, realistic skin texture, natural fabric folds, cinematic lighting, moody atmosphere capturing information overload and multitasking, 8k resolution, photorealistic."

- **`aspect_ratio`** (`AspectRatioEnum`, _optional_):
  Image aspect ratio: 1:1, 3:1, 1:3, 16:9, 9:16, 4:3, 3:4, 3:2, 2:3 Default value: `"1:1"`
  - Default: `"1:1"`
  - Options: `"1:1"`, `"3:1"`, `"1:3"`, `"16:9"`, `"9:16"`, `"4:3"`, `"3:4"`, `"3:2"`, `"2:3"`
  - Examples: "1:1"

- **`seed`** (`integer`, _optional_):
  Seed for generation. 0 and -1 are treated as random.
  - Examples: 0



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
  "seed": 0
}
```


### Output Schema

The API returns the following output format:

- **`images`** (`list<Image>`, _required_):
  Generated image
  - Array of Image
  - Examples: [{"width":2048,"url":"https://v3b.fal.media/files/b/0a961724/CX6N_t6PCQujw0ZxIQMYF_generated_ImagineArt_1_5_Pro.png","height":2048,"content_type":"image/png"}]



**Example Response**:

```json
{
  "images": [
    {
      "width": 2048,
      "url": "https://v3b.fal.media/files/b/0a961724/CX6N_t6PCQujw0ZxIQMYF_generated_ImagineArt_1_5_Pro.png",
      "height": 2048,
      "content_type": "image/png"
    }
  ]
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/imagineart/imagineart-1.5-pro-preview/text-to-image \
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
    "imagineart/imagineart-1.5-pro-preview/text-to-image",
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

const result = await fal.subscribe("imagineart/imagineart-1.5-pro-preview/text-to-image", {
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

- [Model Playground](https://fal.ai/models/imagineart/imagineart-1.5-pro-preview/text-to-image)
- [API Documentation](https://fal.ai/models/imagineart/imagineart-1.5-pro-preview/text-to-image/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=imagineart/imagineart-1.5-pro-preview/text-to-image)

### fal.ai Platform

- [Platform Documentation](https://docs.fal.ai)
- [Python Client](https://docs.fal.ai/clients/python)
- [JavaScript Client](https://docs.fal.ai/clients/javascript)
