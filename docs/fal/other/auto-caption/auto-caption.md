# Auto-Captioner

> Automatically generates text captions for your videos from the audio as per text colour/font specifications


## Overview

- **Endpoint**: `https://fal.run/fal-ai/auto-caption`
- **Model ID**: `fal-ai/auto-caption`
- **Category**: video-to-video
- **Kind**: inference
**Tags**: captioning, video



## Pricing

- **Price**: $0.1 per videos

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`video_url`** (`string`, _required_):
  URL to the .mp4 video with audio. Only videos of size <400MB are allowed.

- **`txt_color`** (`string`, _optional_):
  Colour of the text. Can be a RGB tuple, a color name, or an hexadecimal notation. Default value: `"white"`
  - Default: `"white"`

- **`txt_font`** (`string`, _optional_):
  Font for generated captions. Choose one in 'Arial','Standard','Garamond', 'Times New Roman','Georgia', or pass a url to a .ttf file Default value: `"Standard"`
  - Default: `"Standard"`

- **`font_size`** (`integer`, _optional_):
  Size of text in generated captions. Default value: `24`
  - Default: `24`

- **`stroke_width`** (`integer`, _optional_):
  Width of the text strokes in pixels Default value: `1`
  - Default: `1`

- **`left_align`** (`string | float`, _optional_):
  Left-to-right alignment of the text. Can be a string ('left', 'center', 'right') or a float (0.0-1.0) Default value: `center`
  - Default: `"center"`
  - One of: string | float

- **`top_align`** (`string | float`, _optional_):
  Top-to-bottom alignment of the text. Can be a string ('top', 'center', 'bottom') or a float (0.0-1.0) Default value: `center`
  - Default: `"center"`
  - One of: string | float

- **`refresh_interval`** (`float`, _optional_):
  Number of seconds the captions should stay on screen. A higher number will also result in more text being displayed at once. Default value: `1.5`
  - Default: `1.5`
  - Range: `0.5` to `3`

- **`text_case`** (`TextCaseEnum`, _optional_):
  Capitalization to apply to subtitle text. 'upper' converts text to UPPERCASE, 'lower' converts to lowercase, and 'default' preserves the original casing produced by the speech recognizer. Default value: `"default"`
  - Default: `"default"`
  - Options: `"default"`, `"upper"`, `"lower"`



**Required Parameters Example**:

```json
{
  "video_url": ""
}
```

**Full Example**:

```json
{
  "video_url": "",
  "txt_color": "white",
  "txt_font": "Standard",
  "font_size": 24,
  "stroke_width": 1,
  "left_align": "center",
  "top_align": "center",
  "refresh_interval": 1.5,
  "text_case": "default"
}
```


### Output Schema

The API returns the following output format:

- **`video_url`** (`string`, _required_):
  URL to the caption .mp4 video.



**Example Response**:

```json
{
  "video_url": ""
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/auto-caption \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "video_url": ""
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
    "fal-ai/auto-caption",
    arguments={
        "video_url": ""
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

const result = await fal.subscribe("fal-ai/auto-caption", {
  input: {
    video_url: ""
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

- [Model Playground](https://fal.ai/models/fal-ai/auto-caption)
- [API Documentation](https://fal.ai/models/fal-ai/auto-caption/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/auto-caption)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
