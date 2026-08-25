# Workflow Utilities Auto Subtitle

> Add automatic subtitles to videos


## Overview

- **Endpoint**: `https://fal.run/fal-ai/workflow-utilities/auto-subtitle`
- **Model ID**: `fal-ai/workflow-utilities/auto-subtitle`
- **Category**: video-to-video
- **Kind**: inference
**Tags**: auto-subtitle, captioning



## Pricing

- **Price**: $0.03 per minutes

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`video_url`** (`string`, _required_):
  URL of the video file to add automatic subtitles to
  - Examples: "https://v3b.fal.media/files/b/kangaroo/oUCiZjQwEy6bIQdPUSLDF_output.mp4"

- **`language`** (`string`, _optional_):
  Language code for transcription (e.g., 'en', 'es', 'fr', 'de', 'it', 'pt', 'nl', 'ja', 'zh', 'ko') or 3-letter ISO code (e.g., 'eng', 'spa', 'fra') Default value: `"en"`
  - Default: `"en"`
  - Examples: "en", "es", "fr", "de", "it", "eng", "spa", "fra"

- **`font_name`** (`string`, _optional_):
  Any Google Font name from fonts.google.com (e.g., 'Montserrat', 'Poppins', 'BBH Sans Hegarty') Default value: `"Montserrat"`
  - Default: `"Montserrat"`
  - Examples: "Montserrat", "Poppins", "Bebas Neue", "Oswald", "Inter", "Roboto", "BBH Sans Hegarty"

- **`font_size`** (`integer`, _optional_):
  Font size for subtitles (TikTok style uses larger text) Default value: `100`
  - Default: `100`
  - Range: `20` to `150`

- **`font_weight`** (`FontWeightEnum`, _optional_):
  Font weight (TikTok style typically uses bold or black) Default value: `"bold"`
  - Default: `"bold"`
  - Options: `"normal"`, `"bold"`, `"black"`

- **`font_color`** (`FontColorEnum`, _optional_):
  Subtitle text color for non-active words Default value: `"white"`
  - Default: `"white"`
  - Options: `"white"`, `"black"`, `"red"`, `"green"`, `"blue"`, `"yellow"`, `"orange"`, `"purple"`, `"pink"`, `"brown"`, `"gray"`, `"cyan"`, `"magenta"`

- **`highlight_color`** (`HighlightColorEnum`, _optional_):
  Color for the currently speaking word (karaoke-style highlight) Default value: `"purple"`
  - Default: `"purple"`
  - Options: `"white"`, `"black"`, `"red"`, `"green"`, `"blue"`, `"yellow"`, `"orange"`, `"purple"`, `"pink"`, `"brown"`, `"gray"`, `"cyan"`, `"magenta"`

- **`stroke_width`** (`integer`, _optional_):
  Text stroke/outline width in pixels (0 for no stroke) Default value: `3`
  - Default: `3`
  - Range: `0` to `10`

- **`stroke_color`** (`StrokeColorEnum`, _optional_):
  Text stroke/outline color Default value: `"black"`
  - Default: `"black"`
  - Options: `"black"`, `"white"`, `"red"`, `"green"`, `"blue"`, `"yellow"`, `"orange"`, `"purple"`, `"pink"`, `"brown"`, `"gray"`, `"cyan"`, `"magenta"`

- **`background_color`** (`BackgroundColorEnum`, _optional_):
  Background color behind text ('none' or 'transparent' for no background) Default value: `"none"`
  - Default: `"none"`
  - Options: `"black"`, `"white"`, `"red"`, `"green"`, `"blue"`, `"yellow"`, `"orange"`, `"purple"`, `"pink"`, `"brown"`, `"gray"`, `"cyan"`, `"magenta"`, `"none"`, `"transparent"`

- **`background_opacity`** (`float`, _optional_):
  Background opacity (0.0 = fully transparent, 1.0 = fully opaque)
  - Default: `0`
  - Range: `0` to `1`

- **`position`** (`PositionEnum`, _optional_):
  Vertical position of subtitles Default value: `"bottom"`
  - Default: `"bottom"`
  - Options: `"top"`, `"center"`, `"bottom"`

- **`y_offset`** (`integer`, _optional_):
  Vertical offset in pixels (positive = move down, negative = move up) Default value: `75`
  - Default: `75`
  - Range: `-200` to `200`

- **`words_per_subtitle`** (`integer`, _optional_):
  Maximum number of words per subtitle segment. Use 1 for single-word display, 2-3 for short phrases, or 8-12 for full sentences. Default value: `3`
  - Default: `3`
  - Range: `1` to `12`
  - Examples: 1, 3, 6, 12

- **`enable_animation`** (`boolean`, _optional_):
  Enable animation effects for subtitles (bounce style entrance) Default value: `true`
  - Default: `true`



**Required Parameters Example**:

```json
{
  "video_url": "https://v3b.fal.media/files/b/kangaroo/oUCiZjQwEy6bIQdPUSLDF_output.mp4"
}
```

**Full Example**:

```json
{
  "video_url": "https://v3b.fal.media/files/b/kangaroo/oUCiZjQwEy6bIQdPUSLDF_output.mp4",
  "language": "en",
  "font_name": "Montserrat",
  "font_size": 100,
  "font_weight": "bold",
  "font_color": "white",
  "highlight_color": "purple",
  "stroke_width": 3,
  "stroke_color": "black",
  "background_color": "none",
  "position": "bottom",
  "y_offset": 75,
  "words_per_subtitle": 1,
  "enable_animation": true
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`File`, _required_):
  The video with automatic subtitles
  - Examples: {"file_size":16789234,"file_name":"output.mp4","content_type":"video/mp4","url":"https://v3b.fal.media/files/b/monkey/HPBSoe-QsAxSIkDh7Zn76_output.mp4"}

- **`transcription`** (`string`, _required_):
  Full transcription text

- **`subtitle_count`** (`integer`, _required_):
  Number of subtitle segments generated

- **`words`** (`list<object>`, _optional_):
  Word-level timing information from transcription service
  - Array of object

- **`transcription_metadata`** (`object`, _optional_):
  Additional transcription metadata from ElevenLabs (language, segments, etc.)



**Example Response**:

```json
{
  "video": {
    "file_size": 16789234,
    "file_name": "output.mp4",
    "content_type": "video/mp4",
    "url": "https://v3b.fal.media/files/b/monkey/HPBSoe-QsAxSIkDh7Zn76_output.mp4"
  },
  "transcription": ""
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/workflow-utilities/auto-subtitle \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "video_url": "https://v3b.fal.media/files/b/kangaroo/oUCiZjQwEy6bIQdPUSLDF_output.mp4"
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
    "fal-ai/workflow-utilities/auto-subtitle",
    arguments={
        "video_url": "https://v3b.fal.media/files/b/kangaroo/oUCiZjQwEy6bIQdPUSLDF_output.mp4"
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

const result = await fal.subscribe("fal-ai/workflow-utilities/auto-subtitle", {
  input: {
    video_url: "https://v3b.fal.media/files/b/kangaroo/oUCiZjQwEy6bIQdPUSLDF_output.mp4"
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

- [Model Playground](https://fal.ai/models/fal-ai/workflow-utilities/auto-subtitle)
- [API Documentation](https://fal.ai/models/fal-ai/workflow-utilities/auto-subtitle/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/workflow-utilities/auto-subtitle)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
