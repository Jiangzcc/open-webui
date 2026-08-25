# Heygen

> Heygen Translate Model with Extreme Speed


## Overview

- **Endpoint**: `https://fal.run/fal-ai/heygen/v2/translate/speed`
- **Model ID**: `fal-ai/heygen/v2/translate/speed`
- **Category**: video-to-video
- **Kind**: inference
**Tags**: video-to-video



## Pricing

Your request will cost **$0.05** per output video second.

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`video_url`** (`string`, _required_):
  URL of the video to translate. Maximum length is 8 minutes.
  - Examples: "https://v3b.fal.media/files/b/0a9004c7/FM7Q5tK2b59x66Bl8HC0Z_vt-lang-en.mp4"

- **`output_language`** (`OutputLanguageEnum`, _required_):
  The target language to translate the video into
  - Options: `"English"`, `"Spanish"`, `"French"`, `"Hindi"`, `"Italian"`, `"German"`, `"Polish"`, `"Portuguese"`, `"Chinese"`, `"Japanese"`, `"Dutch"`, `"Turkish"`, `"Korean"`, `"Danish"`, `"Arabic"`, `"Romanian"`, `"Mandarin"`, `"Filipino"`, `"Swedish"`, `"Indonesian"`, `"Ukrainian"`, `"Greek"`, `"Czech"`, `"Bulgarian"`, `"Malay"`, `"Slovak"`, `"Croatian"`, `"Tamil"`, `"Finnish"`, `"Russian"`, `"Afrikaans (South Africa)"`, `"Albanian (Albania)"`, `"Amharic (Ethiopia)"`, `"Arabic (Algeria)"`, `"Arabic (Bahrain)"`, `"Arabic (Egypt)"`, `"Arabic (Iraq)"`, `"Arabic (Jordan)"`, `"Arabic (Kuwait)"`, `"Arabic (Lebanon)"`, `"Arabic (Libya)"`, `"Arabic (Morocco)"`, `"Arabic (Oman)"`, `"Arabic (Qatar)"`, `"Arabic (Saudi Arabia)"`, `"Arabic (Syria)"`, `"Arabic (Tunisia)"`, `"Arabic (United Arab Emirates)"`, `"Arabic (Yemen)"`, `"Armenian (Armenia)"`, `"Azerbaijani (Latin, Azerbaijan)"`, `"Bangla (Bangladesh)"`, `"Basque"`, `"Bengali (India)"`, `"Bosnian (Bosnia and Herzegovina)"`, `"Bulgarian (Bulgaria)"`, `"Burmese (Myanmar)"`, `"Catalan"`, `"Chinese (Cantonese, Traditional)"`, `"Chinese (Jilu Mandarin, Simplified)"`, `"Chinese (Mandarin, Simplified)"`, `"Chinese (Northeastern Mandarin, Simplified)"`, `"Chinese (Southwestern Mandarin, Simplified)"`, `"Chinese (Taiwanese Mandarin, Traditional)"`, `"Chinese (Wu, Simplified)"`, `"Chinese (Zhongyuan Mandarin Henan, Simplified)"`, `"Chinese (Zhongyuan Mandarin Shaanxi, Simplified)"`, `"Croatian (Croatia)"`, `"Czech (Czechia)"`, `"Danish (Denmark)"`, `"Dutch (Belgium)"`, `"Dutch (Netherlands)"`, `"English (Australia)"`, `"English (Canada)"`, `"English (Hong Kong SAR)"`, `"English (India)"`, `"English (Ireland)"`, `"English (Kenya)"`, `"English (New Zealand)"`, `"English (Nigeria)"`, `"English (Philippines)"`, `"English (Singapore)"`, `"English (South Africa)"`, `"English (Tanzania)"`, `"English (UK)"`, `"English (United States)"`, `"Estonian (Estonia)"`, `"Filipino (Philippines)"`, `"Finnish (Finland)"`, `"French (Belgium)"`, `"French (Canada)"`, `"French (France)"`, `"French (Switzerland)"`, `"Galician"`, `"Georgian (Georgia)"`, `"German (Austria)"`, `"German (Germany)"`, `"German (Switzerland)"`, `"Greek (Greece)"`, `"Gujarati (India)"`, `"Hebrew (Israel)"`, `"Hindi (India)"`, `"Hungarian (Hungary)"`, `"Icelandic (Iceland)"`, `"Indonesian (Indonesia)"`, `"Irish (Ireland)"`, `"Italian (Italy)"`, `"Japanese (Japan)"`, `"Javanese (Latin, Indonesia)"`, `"Kannada (India)"`, `"Kazakh (Kazakhstan)"`, `"Khmer (Cambodia)"`, `"Korean (Korea)"`, `"Lao (Laos)"`, `"Latvian (Latvia)"`, `"Lithuanian (Lithuania)"`, `"Macedonian (North Macedonia)"`, `"Malay (Malaysia)"`, `"Malayalam (India)"`, `"Maltese (Malta)"`, `"Marathi (India)"`, `"Mongolian (Mongolia)"`, `"Nepali (Nepal)"`, `"Norwegian Bokmål (Norway)"`, `"Pashto (Afghanistan)"`, `"Persian (Iran)"`, `"Polish (Poland)"`, `"Portuguese (Brazil)"`, `"Portuguese (Portugal)"`, `"Romanian (Romania)"`, `"Russian (Russia)"`, `"Serbian (Latin, Serbia)"`, `"Sinhala (Sri Lanka)"`, `"Slovak (Slovakia)"`, `"Slovenian (Slovenia)"`, `"Somali (Somalia)"`, `"Spanish (Argentina)"`, `"Spanish (Bolivia)"`, `"Spanish (Chile)"`, `"Spanish (Colombia)"`, `"Spanish (Costa Rica)"`, `"Spanish (Cuba)"`, `"Spanish (Dominican Republic)"`, `"Spanish (Ecuador)"`, `"Spanish (El Salvador)"`, `"Spanish (Equatorial Guinea)"`, `"Spanish (Guatemala)"`, `"Spanish (Honduras)"`, `"Spanish (Mexico)"`, `"Spanish (Nicaragua)"`, `"Spanish (Panama)"`, `"Spanish (Paraguay)"`, `"Spanish (Peru)"`, `"Spanish (Puerto Rico)"`, `"Spanish (Spain)"`, `"Spanish (United States)"`, `"Spanish (Uruguay)"`, `"Spanish (Venezuela)"`, `"Sundanese (Indonesia)"`, `"Swahili (Kenya)"`, `"Swahili (Tanzania)"`, `"Swedish (Sweden)"`, `"Tamil (India)"`, `"Tamil (Malaysia)"`, `"Tamil (Singapore)"`, `"Tamil (Sri Lanka)"`, `"Telugu (India)"`, `"Thai (Thailand)"`, `"Turkish (Türkiye)"`, `"Ukrainian (Ukraine)"`, `"Urdu (India)"`, `"Urdu (Pakistan)"`, `"Uzbek (Latin, Uzbekistan)"`, `"Vietnamese (Vietnam)"`, `"Welsh (United Kingdom)"`, `"Zulu (South Africa)"`, `"English - Your Accent"`, `"English - American Accent"`
  - Examples: "Spanish"

- **`translate_audio_only`** (`boolean`, _optional_):
  Translate only the audio, ignore the faces and only translate the voice track
  - Default: `false`

- **`speaker_num`** (`integer`, _optional_):
  Number of speakers in the video

- **`enable_dynamic_duration`** (`boolean`, _optional_):
  Enable dynamic duration to enhance conversational fluidity between languages with different speaking rates Default value: `true`
  - Default: `true`

- **`brand_glossary_id`** (`string`, _optional_):
  HeyGen brand glossary ID for custom term translations.

- **`srt_url`** (`string`, _optional_):
  Optional URL of a custom SRT subtitle file.

- **`srt_role`** (`Enum`, _optional_):
  Whether the custom SRT applies to the source or translated video.
  - Options: `"input"`, `"output"`

- **`enable_caption`** (`boolean`, _optional_):
  Generate an SRT caption file alongside the translated video.
  - Default: `false`



**Required Parameters Example**:

```json
{
  "video_url": "https://v3b.fal.media/files/b/0a9004c7/FM7Q5tK2b59x66Bl8HC0Z_vt-lang-en.mp4",
  "output_language": "Spanish"
}
```

**Full Example**:

```json
{
  "video_url": "https://v3b.fal.media/files/b/0a9004c7/FM7Q5tK2b59x66Bl8HC0Z_vt-lang-en.mp4",
  "output_language": "Spanish",
  "enable_dynamic_duration": true
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`File`, _required_):
  The translated video file
  - Examples: {"url":"https://v3b.fal.media/files/b/0a900522/WZRPanS88KdyIhYfqP_Md_output.mp4"}

- **`caption_file`** (`File`, _optional_):
  Generated SRT captions when enable_caption is true.



**Example Response**:

```json
{
  "video": {
    "url": "https://v3b.fal.media/files/b/0a900522/WZRPanS88KdyIhYfqP_Md_output.mp4"
  }
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/heygen/v2/translate/speed \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "video_url": "https://v3b.fal.media/files/b/0a9004c7/FM7Q5tK2b59x66Bl8HC0Z_vt-lang-en.mp4",
     "output_language": "Spanish"
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
    "fal-ai/heygen/v2/translate/speed",
    arguments={
        "video_url": "https://v3b.fal.media/files/b/0a9004c7/FM7Q5tK2b59x66Bl8HC0Z_vt-lang-en.mp4",
        "output_language": "Spanish"
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

const result = await fal.subscribe("fal-ai/heygen/v2/translate/speed", {
  input: {
    video_url: "https://v3b.fal.media/files/b/0a9004c7/FM7Q5tK2b59x66Bl8HC0Z_vt-lang-en.mp4",
    output_language: "Spanish"
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

- [Model Playground](https://fal.ai/models/fal-ai/heygen/v2/translate/speed)
- [API Documentation](https://fal.ai/models/fal-ai/heygen/v2/translate/speed/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/heygen/v2/translate/speed)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
