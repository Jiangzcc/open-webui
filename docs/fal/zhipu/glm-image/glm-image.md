# GLM Image

> Create high-quality images with accurate text rendering and rich knowledge details—supports editing, style transfer, and maintaining consistent characters across multiple images.


## Overview

- **Endpoint**: `https://fal.run/fal-ai/glm-image`
- **Model ID**: `fal-ai/glm-image`
- **Category**: text-to-image
- **Kind**: inference
**Tags**: text-to-image



## Pricing

- **Price**: $0.05 per megapixels

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _required_):
  Text prompt for image generation.
  - Examples: "An elegant close-up photograph of hands holding a beautifully illustrated watercolor menu card. The hands have natural sun-kissed skin with a delicate gold ring, gripping the menu gently and refined.\n\nThe menu is a work of art—hand-painted watercolor illustration on textured cream watercolor paper with soft deckled edges:\n\n- Top: \"AZURE\" painted in flowing navy blue watercolor calligraphy with organic brushstroke texture and slight color bleeding\n- Watercolor illustration border: delicate tropical elements painted in soft washes—translucent turquoise waves flowing along the edges, loose coral and pink hibiscus flowers in the corners, gentle green palm leaf strokes, and small golden paint splatters suggesting sunlight\n- Center menu items in elegant hand-lettered watercolor script with slight variations in ink density:\n\n  \"Tuna Tartare — 24\"\n  \"Sea Bass — 32\"\n  \"Mango Pavlova — 14\"\n\n- Bottom: \"Koh Samui\" in small watercolor lettering with a tiny painted wave\n\nThe watercolor has beautiful organic qualities—soft color gradients, natural paper texture visible through transparent washes, slight bleeding at edges of brushstrokes, layered translucent blues and greens creating depth. The paint has a luminous, fresh quality with white paper showing through in places.\n\nBackground: dreamy out-of-focus turquoise ocean with sparkling bokeh lights reflecting off water, creating soft circular light spots in aqua and gold tones. The blurred background complements the watercolor aesthetic perfectly.\n\nLighting: warm natural golden hour sunlight from upper left, illuminating the watercolor pigments and making them glow. The light catches the textured watercolor paper beautifully, showing subtle shadows in the paint layers and paper grain.\n\nPhotography style: shot on 85mm f/1.4, shallow depth of field with only the menu in sharp focus. High-end editorial aesthetic that celebrates the handmade, artistic quality of the watercolor. Color palette: cream paper, translucent turquoise and teal watercolors, soft coral pink, navy blue, gentle greens, golden accents, warm skin tones.\n\nThe overall mood is artistic, luxurious, handcrafted—like a boutique resort that values artistry and craftsmanship. The watercolor style feels fresh, organic, and elevated."

- **`image_size`** (`ImageSize | Enum`, _optional_):
  Output image size. Default value: `square_hd`
  - Default: `"square_hd"`
  - One of: ImageSize | Enum

- **`num_inference_steps`** (`integer`, _optional_):
  Number of diffusion denoising steps. More steps generally produce higher quality images. Default value: `30`
  - Default: `30`
  - Range: `10` to `100`

- **`guidance_scale`** (`float`, _optional_):
  Classifier-free guidance scale. Higher values make the model follow the prompt more closely. Default value: `1.5`
  - Default: `1.5`
  - Range: `1` to `10`

- **`seed`** (`integer`, _optional_):
  Random seed for reproducibility. The same seed with the same prompt will produce the same image.

- **`num_images`** (`integer`, _optional_):
  Number of images to generate. Default value: `1`
  - Default: `1`
  - Range: `1` to `4`

- **`enable_safety_checker`** (`boolean`, _optional_):
  Enable NSFW safety checking on the generated images. Default value: `true`
  - Default: `true`

- **`output_format`** (`OutputFormatEnum`, _optional_):
  Output image format. Default value: `"jpeg"`
  - Default: `"jpeg"`
  - Options: `"jpeg"`, `"png"`

- **`sync_mode`** (`boolean`, _optional_):
  If True, the image will be returned as a base64 data URI instead of a URL.
  - Default: `false`

- **`enable_prompt_expansion`** (`boolean`, _optional_):
  If True, the prompt will be enhanced using an LLM for more detailed and higher quality results.
  - Default: `false`



**Required Parameters Example**:

```json
{
  "prompt": "An elegant close-up photograph of hands holding a beautifully illustrated watercolor menu card. The hands have natural sun-kissed skin with a delicate gold ring, gripping the menu gently and refined.\n\nThe menu is a work of art—hand-painted watercolor illustration on textured cream watercolor paper with soft deckled edges:\n\n- Top: \"AZURE\" painted in flowing navy blue watercolor calligraphy with organic brushstroke texture and slight color bleeding\n- Watercolor illustration border: delicate tropical elements painted in soft washes—translucent turquoise waves flowing along the edges, loose coral and pink hibiscus flowers in the corners, gentle green palm leaf strokes, and small golden paint splatters suggesting sunlight\n- Center menu items in elegant hand-lettered watercolor script with slight variations in ink density:\n\n  \"Tuna Tartare — 24\"\n  \"Sea Bass — 32\"\n  \"Mango Pavlova — 14\"\n\n- Bottom: \"Koh Samui\" in small watercolor lettering with a tiny painted wave\n\nThe watercolor has beautiful organic qualities—soft color gradients, natural paper texture visible through transparent washes, slight bleeding at edges of brushstrokes, layered translucent blues and greens creating depth. The paint has a luminous, fresh quality with white paper showing through in places.\n\nBackground: dreamy out-of-focus turquoise ocean with sparkling bokeh lights reflecting off water, creating soft circular light spots in aqua and gold tones. The blurred background complements the watercolor aesthetic perfectly.\n\nLighting: warm natural golden hour sunlight from upper left, illuminating the watercolor pigments and making them glow. The light catches the textured watercolor paper beautifully, showing subtle shadows in the paint layers and paper grain.\n\nPhotography style: shot on 85mm f/1.4, shallow depth of field with only the menu in sharp focus. High-end editorial aesthetic that celebrates the handmade, artistic quality of the watercolor. Color palette: cream paper, translucent turquoise and teal watercolors, soft coral pink, navy blue, gentle greens, golden accents, warm skin tones.\n\nThe overall mood is artistic, luxurious, handcrafted—like a boutique resort that values artistry and craftsmanship. The watercolor style feels fresh, organic, and elevated."
}
```

**Full Example**:

```json
{
  "prompt": "An elegant close-up photograph of hands holding a beautifully illustrated watercolor menu card. The hands have natural sun-kissed skin with a delicate gold ring, gripping the menu gently and refined.\n\nThe menu is a work of art—hand-painted watercolor illustration on textured cream watercolor paper with soft deckled edges:\n\n- Top: \"AZURE\" painted in flowing navy blue watercolor calligraphy with organic brushstroke texture and slight color bleeding\n- Watercolor illustration border: delicate tropical elements painted in soft washes—translucent turquoise waves flowing along the edges, loose coral and pink hibiscus flowers in the corners, gentle green palm leaf strokes, and small golden paint splatters suggesting sunlight\n- Center menu items in elegant hand-lettered watercolor script with slight variations in ink density:\n\n  \"Tuna Tartare — 24\"\n  \"Sea Bass — 32\"\n  \"Mango Pavlova — 14\"\n\n- Bottom: \"Koh Samui\" in small watercolor lettering with a tiny painted wave\n\nThe watercolor has beautiful organic qualities—soft color gradients, natural paper texture visible through transparent washes, slight bleeding at edges of brushstrokes, layered translucent blues and greens creating depth. The paint has a luminous, fresh quality with white paper showing through in places.\n\nBackground: dreamy out-of-focus turquoise ocean with sparkling bokeh lights reflecting off water, creating soft circular light spots in aqua and gold tones. The blurred background complements the watercolor aesthetic perfectly.\n\nLighting: warm natural golden hour sunlight from upper left, illuminating the watercolor pigments and making them glow. The light catches the textured watercolor paper beautifully, showing subtle shadows in the paint layers and paper grain.\n\nPhotography style: shot on 85mm f/1.4, shallow depth of field with only the menu in sharp focus. High-end editorial aesthetic that celebrates the handmade, artistic quality of the watercolor. Color palette: cream paper, translucent turquoise and teal watercolors, soft coral pink, navy blue, gentle greens, golden accents, warm skin tones.\n\nThe overall mood is artistic, luxurious, handcrafted—like a boutique resort that values artistry and craftsmanship. The watercolor style feels fresh, organic, and elevated.",
  "image_size": "square_hd",
  "num_inference_steps": 30,
  "guidance_scale": 1.5,
  "num_images": 1,
  "enable_safety_checker": true,
  "output_format": "jpeg"
}
```


### Output Schema

The API returns the following output format:

- **`images`** (`list<Image>`, _required_):
  List of URLs to the generated images.
  - Array of Image
  - Examples: [{"content_type":"image/jpeg","width":1024,"height":1024,"url":"https://storage.googleapis.com/falserverless/example_outputs/menu.jpg"}]

- **`timings`** (`Timings`, _required_)

- **`seed`** (`integer`, _required_):
  Seed of the generated Image. It will be the same value of the one passed in the
  input or the randomly generated that was used in case none was passed.

- **`has_nsfw_concepts`** (`list<boolean>`, _required_):
  Whether the generated images contain NSFW concepts.
  - Array of boolean

- **`prompt`** (`string`, _required_):
  The prompt used for generating the image.



**Example Response**:

```json
{
  "images": [
    {
      "content_type": "image/jpeg",
      "width": 1024,
      "height": 1024,
      "url": "https://storage.googleapis.com/falserverless/example_outputs/menu.jpg"
    }
  ],
  "prompt": ""
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/glm-image \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "An elegant close-up photograph of hands holding a beautifully illustrated watercolor menu card. The hands have natural sun-kissed skin with a delicate gold ring, gripping the menu gently and refined.\n\nThe menu is a work of art—hand-painted watercolor illustration on textured cream watercolor paper with soft deckled edges:\n\n- Top: \"AZURE\" painted in flowing navy blue watercolor calligraphy with organic brushstroke texture and slight color bleeding\n- Watercolor illustration border: delicate tropical elements painted in soft washes—translucent turquoise waves flowing along the edges, loose coral and pink hibiscus flowers in the corners, gentle green palm leaf strokes, and small golden paint splatters suggesting sunlight\n- Center menu items in elegant hand-lettered watercolor script with slight variations in ink density:\n\n  \"Tuna Tartare — 24\"\n  \"Sea Bass — 32\"\n  \"Mango Pavlova — 14\"\n\n- Bottom: \"Koh Samui\" in small watercolor lettering with a tiny painted wave\n\nThe watercolor has beautiful organic qualities—soft color gradients, natural paper texture visible through transparent washes, slight bleeding at edges of brushstrokes, layered translucent blues and greens creating depth. The paint has a luminous, fresh quality with white paper showing through in places.\n\nBackground: dreamy out-of-focus turquoise ocean with sparkling bokeh lights reflecting off water, creating soft circular light spots in aqua and gold tones. The blurred background complements the watercolor aesthetic perfectly.\n\nLighting: warm natural golden hour sunlight from upper left, illuminating the watercolor pigments and making them glow. The light catches the textured watercolor paper beautifully, showing subtle shadows in the paint layers and paper grain.\n\nPhotography style: shot on 85mm f/1.4, shallow depth of field with only the menu in sharp focus. High-end editorial aesthetic that celebrates the handmade, artistic quality of the watercolor. Color palette: cream paper, translucent turquoise and teal watercolors, soft coral pink, navy blue, gentle greens, golden accents, warm skin tones.\n\nThe overall mood is artistic, luxurious, handcrafted—like a boutique resort that values artistry and craftsmanship. The watercolor style feels fresh, organic, and elevated."
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
    "fal-ai/glm-image",
    arguments={
        "prompt": "An elegant close-up photograph of hands holding a beautifully illustrated watercolor menu card. The hands have natural sun-kissed skin with a delicate gold ring, gripping the menu gently and refined.

    The menu is a work of art—hand-painted watercolor illustration on textured cream watercolor paper with soft deckled edges:

    - Top: \"AZURE\" painted in flowing navy blue watercolor calligraphy with organic brushstroke texture and slight color bleeding
    - Watercolor illustration border: delicate tropical elements painted in soft washes—translucent turquoise waves flowing along the edges, loose coral and pink hibiscus flowers in the corners, gentle green palm leaf strokes, and small golden paint splatters suggesting sunlight
    - Center menu items in elegant hand-lettered watercolor script with slight variations in ink density:

      \"Tuna Tartare — 24\"
      \"Sea Bass — 32\"
      \"Mango Pavlova — 14\"

    - Bottom: \"Koh Samui\" in small watercolor lettering with a tiny painted wave

    The watercolor has beautiful organic qualities—soft color gradients, natural paper texture visible through transparent washes, slight bleeding at edges of brushstrokes, layered translucent blues and greens creating depth. The paint has a luminous, fresh quality with white paper showing through in places.

    Background: dreamy out-of-focus turquoise ocean with sparkling bokeh lights reflecting off water, creating soft circular light spots in aqua and gold tones. The blurred background complements the watercolor aesthetic perfectly.

    Lighting: warm natural golden hour sunlight from upper left, illuminating the watercolor pigments and making them glow. The light catches the textured watercolor paper beautifully, showing subtle shadows in the paint layers and paper grain.

    Photography style: shot on 85mm f/1.4, shallow depth of field with only the menu in sharp focus. High-end editorial aesthetic that celebrates the handmade, artistic quality of the watercolor. Color palette: cream paper, translucent turquoise and teal watercolors, soft coral pink, navy blue, gentle greens, golden accents, warm skin tones.

    The overall mood is artistic, luxurious, handcrafted—like a boutique resort that values artistry and craftsmanship. The watercolor style feels fresh, organic, and elevated."
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

const result = await fal.subscribe("fal-ai/glm-image", {
  input: {
    prompt: "An elegant close-up photograph of hands holding a beautifully illustrated watercolor menu card. The hands have natural sun-kissed skin with a delicate gold ring, gripping the menu gently and refined.

  The menu is a work of art—hand-painted watercolor illustration on textured cream watercolor paper with soft deckled edges:

  - Top: \"AZURE\" painted in flowing navy blue watercolor calligraphy with organic brushstroke texture and slight color bleeding
  - Watercolor illustration border: delicate tropical elements painted in soft washes—translucent turquoise waves flowing along the edges, loose coral and pink hibiscus flowers in the corners, gentle green palm leaf strokes, and small golden paint splatters suggesting sunlight
  - Center menu items in elegant hand-lettered watercolor script with slight variations in ink density:

    \"Tuna Tartare — 24\"
    \"Sea Bass — 32\"
    \"Mango Pavlova — 14\"

  - Bottom: \"Koh Samui\" in small watercolor lettering with a tiny painted wave

  The watercolor has beautiful organic qualities—soft color gradients, natural paper texture visible through transparent washes, slight bleeding at edges of brushstrokes, layered translucent blues and greens creating depth. The paint has a luminous, fresh quality with white paper showing through in places.

  Background: dreamy out-of-focus turquoise ocean with sparkling bokeh lights reflecting off water, creating soft circular light spots in aqua and gold tones. The blurred background complements the watercolor aesthetic perfectly.

  Lighting: warm natural golden hour sunlight from upper left, illuminating the watercolor pigments and making them glow. The light catches the textured watercolor paper beautifully, showing subtle shadows in the paint layers and paper grain.

  Photography style: shot on 85mm f/1.4, shallow depth of field with only the menu in sharp focus. High-end editorial aesthetic that celebrates the handmade, artistic quality of the watercolor. Color palette: cream paper, translucent turquoise and teal watercolors, soft coral pink, navy blue, gentle greens, golden accents, warm skin tones.

  The overall mood is artistic, luxurious, handcrafted—like a boutique resort that values artistry and craftsmanship. The watercolor style feels fresh, organic, and elevated."
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

- [Model Playground](https://fal.ai/models/fal-ai/glm-image)
- [API Documentation](https://fal.ai/models/fal-ai/glm-image/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/glm-image)

### fal.ai Platform

- [Platform Documentation](https://docs.fal.ai)
- [Python Client](https://docs.fal.ai/clients/python)
- [JavaScript Client](https://docs.fal.ai/clients/javascript)
