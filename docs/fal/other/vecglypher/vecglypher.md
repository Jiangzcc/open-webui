# Vecglypher

> Vector font generation with VecGlypher. Create custom glyphs from text descriptions or reference images—outputs clean SVG paths directly without raster-to-vector conversion.


## Overview

- **Endpoint**: `https://fal.run/fal-ai/vecglypher`
- **Model ID**: `fal-ai/vecglypher`
- **Category**: text-to-image
- **Kind**: inference


## Pricing

- **Price**: $0.005 per images

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _required_):
  The target text to generate as vector glyphs. Each character is rendered as a separate SVG path element.
  - Examples: "g"

- **`style_description`** (`string`, _optional_):
  Font style description using typography terms such as weight (100-900), style (italic, oblique), category (serif, sans-serif, display, handwriting, monospace), and characteristics (geometric, humanist, condensed, rounded). Default value: `"italic style, 400 weight, serif, text, elegant"`
  - Default: `"italic style, 400 weight, serif, text, elegant"`
  - Examples: "italic style, 400 weight, serif, text, elegant"

- **`temperature`** (`float`, _optional_):
  Sampling temperature. Lower values produce more deterministic output. Default value: `0.1`
  - Default: `0.1`
  - Range: `0` to `2`

- **`seed`** (`integer`, _optional_):
  Random seed for reproducibility.

- **`enable_safety_checker`** (`boolean`, _optional_):
  Enable input safety checking. Default value: `true`
  - Default: `true`

- **`top_p`** (`float`, _optional_):
  Top-p (nucleus) sampling parameter. Default value: `0.95`
  - Default: `0.95`
  - Range: `0` to `1`

- **`top_k`** (`integer`, _optional_):
  Top-k sampling parameter. Default value: `5`
  - Default: `5`
  - Range: `-1` to `100`

- **`repetition_penalty`** (`float`, _optional_):
  Repetition penalty to reduce repeated SVG path segments. Default value: `1`
  - Default: `1`
  - Range: `0` to `2`

- **`max_tokens`** (`integer`, _optional_):
  Maximum tokens to generate. Increase for longer text. Default value: `8192`
  - Default: `8192`
  - Range: `256` to `16384`

- **`output_size`** (`integer`, _optional_):
  Maximum dimension (width or height) of the output SVG in pixels. The aspect ratio is preserved. Default value: `512`
  - Default: `512`
  - Range: `64` to `4096`

- **`fill_color`** (`string`, _optional_):
  Fill color for the generated glyphs. Accepts any valid SVG/CSS color value. Default value: `"black"`
  - Default: `"black"`
  - Examples: "black", "#FF5733", "rgb(255,87,51)", "none"

- **`stroke_color`** (`string`, _optional_):
  Optional stroke (outline) color for the generated glyphs. When set, adds an outline around each glyph path.
  - Examples: "black", "#333333", "none"

- **`stroke_width`** (`float`, _optional_):
  Stroke width in SVG units. Only applies when stroke_color is set. Default value: `1`
  - Default: `1`
  - Range: `0.1` to `50`



**Required Parameters Example**:

```json
{
  "prompt": "g"
}
```

**Full Example**:

```json
{
  "prompt": "g",
  "style_description": "italic style, 400 weight, serif, text, elegant",
  "temperature": 0.1,
  "enable_safety_checker": true,
  "top_p": 0.95,
  "top_k": 5,
  "repetition_penalty": 1,
  "max_tokens": 8192,
  "output_size": 512,
  "fill_color": "black",
  "stroke_color": "black",
  "stroke_width": 1
}
```


### Output Schema

The API returns the following output format:

- **`image`** (`File`, _required_):
  The generated SVG file containing vector glyphs.
  - Examples: {"content_type":"image/svg+xml","file_size":959,"file_name":"180c718ac5d8407092d0688ea2605f0c.svg","url":"https://v3b.fal.media/files/b/0a90bfc3/0f8Su2aQUzPQy4NZMDQpp_180c718ac5d8407092d0688ea2605f0c.svg"}

- **`svg_content`** (`string`, _required_):
  Raw SVG content as a string.

- **`seed`** (`integer`, _required_):
  The seed used for generation.
  - Examples: 1835785439

- **`timings`** (`Timings`, _required_):
  Timing breakdown of the generation process.
  - Examples: {"inference":10.83}



**Example Response**:

```json
{
  "image": {
    "content_type": "image/svg+xml",
    "file_size": 959,
    "file_name": "180c718ac5d8407092d0688ea2605f0c.svg",
    "url": "https://v3b.fal.media/files/b/0a90bfc3/0f8Su2aQUzPQy4NZMDQpp_180c718ac5d8407092d0688ea2605f0c.svg"
  },
  "svg_content": "",
  "seed": 1835785439,
  "timings": {
    "inference": 10.83
  }
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/vecglypher \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "g"
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
    "fal-ai/vecglypher",
    arguments={
        "prompt": "g"
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

const result = await fal.subscribe("fal-ai/vecglypher", {
  input: {
    prompt: "g"
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

- [Model Playground](https://fal.ai/models/fal-ai/vecglypher)
- [API Documentation](https://fal.ai/models/fal-ai/vecglypher/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/vecglypher)

### fal.ai Platform

- [Platform Documentation](https://docs.fal.ai)
- [Python Client](https://docs.fal.ai/clients/python)
- [JavaScript Client](https://docs.fal.ai/clients/javascript)
