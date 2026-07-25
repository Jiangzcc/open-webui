# Recraft 20b

> Recraft 20b is a new and affordable text-to-image model.


## Overview

- **Endpoint**: `https://fal.run/fal-ai/recraft-20b`
- **Model ID**: `fal-ai/recraft-20b`
- **Category**: text-to-image
- **Kind**: inference
**Tags**: image generation, vector art, typograph, style



## Pricing

Your request will cost **$0.022** per image (or **$0.044** if you are using a vector style). For $1 you can run this model approximately **45** times.

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _required_)
  - Examples: "a red panda in Kyoto"

- **`image_size`** (`ImageSize | Enum`, _optional_):
   Default value: `square_hd`
  - Default: `"square_hd"`
  - One of: ImageSize | Enum

- **`style`** (`StyleEnum`, _optional_):
  The style of the generated images. Vector images cost 2X as much. Default value: `"realistic_image"`
  - Default: `"realistic_image"`
  - Options: `"any"`, `"realistic_image"`, `"digital_illustration"`, `"vector_illustration"`, `"realistic_image/b_and_w"`, `"realistic_image/enterprise"`, `"realistic_image/hard_flash"`, `"realistic_image/hdr"`, `"realistic_image/motion_blur"`, `"realistic_image/natural_light"`, `"realistic_image/studio_portrait"`, `"digital_illustration/2d_art_poster"`, `"digital_illustration/2d_art_poster_2"`, `"digital_illustration/3d"`, `"digital_illustration/80s"`, `"digital_illustration/engraving_color"`, `"digital_illustration/glow"`, `"digital_illustration/grain"`, `"digital_illustration/hand_drawn"`, `"digital_illustration/hand_drawn_outline"`, `"digital_illustration/handmade_3d"`, `"digital_illustration/infantile_sketch"`, `"digital_illustration/kawaii"`, `"digital_illustration/pixel_art"`, `"digital_illustration/psychedelic"`, `"digital_illustration/seamless"`, `"digital_illustration/voxel"`, `"digital_illustration/watercolor"`, `"vector_illustration/cartoon"`, `"vector_illustration/doodle_line_art"`, `"vector_illustration/engraving"`, `"vector_illustration/flat_2"`, `"vector_illustration/kawaii"`, `"vector_illustration/line_art"`, `"vector_illustration/line_circuit"`, `"vector_illustration/linocut"`, `"vector_illustration/seamless"`

- **`colors`** (`list<RGBColor>`, _optional_):
  An array of preferable colors
  - Default: `[]`
  - Array of RGBColor

- **`style_id`** (`string`, _optional_):
  The ID of the custom style reference (optional)

- **`enable_safety_checker`** (`boolean`, _optional_):
  If set to true, the safety checker will be enabled.
  - Default: `false`



**Required Parameters Example**:

```json
{
  "prompt": "a red panda in Kyoto"
}
```

**Full Example**:

```json
{
  "prompt": "a red panda in Kyoto",
  "image_size": "square_hd",
  "style": "realistic_image",
  "colors": []
}
```


### Output Schema

The API returns the following output format:

- **`images`** (`list<File>`, _required_)
  - Array of File
  - Examples: [{"url":"https://fal.media/files/tiger/qeO5RlXiAsdCREUMYg5ZU_image.webp"}]



**Example Response**:

```json
{
  "images": [
    {
      "url": "https://fal.media/files/tiger/qeO5RlXiAsdCREUMYg5ZU_image.webp"
    }
  ]
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/recraft-20b \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "a red panda in Kyoto"
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
    "fal-ai/recraft-20b",
    arguments={
        "prompt": "a red panda in Kyoto"
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

const result = await fal.subscribe("fal-ai/recraft-20b", {
  input: {
    prompt: "a red panda in Kyoto"
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

- [Model Playground](https://fal.ai/models/fal-ai/recraft-20b)
- [API Documentation](https://fal.ai/models/fal-ai/recraft-20b/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/recraft-20b)

### fal.ai Platform

- [Platform Documentation](https://docs.fal.ai)
- [Python Client](https://docs.fal.ai/clients/python)
- [JavaScript Client](https://docs.fal.ai/clients/javascript)
