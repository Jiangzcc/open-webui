# Subtitles

> VEED’s Subtitles API transforms raw footage into polished, publish-ready content with professional burned-in subtitles starting at a base rate of $0.10 per minute.


## Overview

- **Endpoint**: `https://fal.run/veed/subtitles`
- **Model ID**: `veed/subtitles`
- **Category**: video-to-video
- **Kind**: inference


## Pricing

Your request will cost $0.10 per minute of input video, with a 2x multiplier for resolutions above 1080p and a 2x multiplier for dynamic styling. Setting a translation_language adds a flat +$0.20 / minute surcharge on top. Minimum charge: 1 minute.

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`video_url`** (`string`, _required_):
  Upload or paste a URL to the video you want to subtitle.
  - Examples: "https://v3b.fal.media/files/b/0a967ce5/iARc_J0kLN9OEmiXnxT3l_substyle-example-input.mp4"

- **`preset`** (`PresetEnum`, _required_):
  Each style defines fonts, colors, layout, and animation. Two tiers with different pricing:
  
  - Dynamic presets (2x multiplier): glass, whisper, glide2, fusion, glide, terminal, handwritten, backdrop, backdrop2. Richer, context-aware rendering that adapts to the input.
  - Basic presets (1x multiplier): simple, plain, beans, corpo, boo, shadeplay, casper, capri, lowkey, vinta, diego, ali, slay, kitty, hustle, karl, sprout, flex, mint, rizz, vegas. Fixed, lightweight styling with predictable output.
  - Options: `"glass"`, `"whisper"`, `"glide2"`, `"fusion"`, `"glide"`, `"terminal"`, `"handwritten"`, `"backdrop"`, `"backdrop2"`, `"simple"`, `"plain"`, `"beans"`, `"corpo"`, `"boo"`, `"shadeplay"`, `"casper"`, `"capri"`, `"lowkey"`, `"vinta"`, `"diego"`, `"ali"`, `"slay"`, `"kitty"`, `"hustle"`, `"karl"`, `"sprout"`, `"flex"`, `"mint"`, `"rizz"`, `"vegas"`
  - Examples: "glass"

- **`language`** (`Enum`, _optional_):
  Improves transcription accuracy, and should match the source audio (not output subtitles).
  - Options: `"af-ZA"`, `"am-ET"`, `"ar-AE"`, `"ar-BH"`, `"ar-DZ"`, `"ar-EG"`, `"ar-IL"`, `"ar-IQ"`, `"ar-JO"`, `"ar-KW"`, `"ar-LB"`, `"ar-MA"`, `"ar-OM"`, `"ar-PS"`, `"ar-QA"`, `"ar-SA"`, `"ar-TN"`, `"ast-ES"`, `"az-AZ"`, `"ba"`, `"bas"`, `"be-BY"`, `"bg-BG"`, `"br"`, `"bs-BA"`, `"ca-ES"`, `"ceb-PH"`, `"ckb-IQ"`, `"cs-CZ"`, `"cy-GB"`, `"da-DK"`, `"de-DE"`, `"dyu"`, `"el-GR"`, `"en-AU"`, `"en-GB"`, `"en-IN"`, `"en-NZ"`, `"en-US"`, `"eo"`, `"es-AR"`, `"es-BO"`, `"es-CL"`, `"es-CO"`, `"es-CR"`, `"es-DO"`, `"es-EC"`, `"es-ES"`, `"es-GT"`, `"es-HN"`, `"es-MX"`, `"es-NI"`, `"es-PA"`, `"es-PE"`, `"es-PR"`, `"es-PY"`, `"es-SV"`, `"es-US"`, `"es-UY"`, `"es-VE"`, `"et-EE"`, `"eu-ES"`, `"fa-IR"`, `"ff"`, `"fi-FI"`, `"fil-PH"`, `"fo"`, `"fr-CA"`, `"fr-FR"`, `"fy"`, `"ga"`, `"gd"`, `"gl-ES"`, `"ha-NG"`, `"haw"`, `"he-IL"`, `"hr-HR"`, `"hsb"`, `"ht"`, `"hu-HU"`, `"hy-AM"`, `"id-ID"`, `"ig"`, `"is-IS"`, `"it-IT"`, `"ja-JP"`, `"ja-Latn-JP"`, `"jv-ID"`, `"ka-GE"`, `"kab"`, `"kam-KE"`, `"kea-CV"`, `"kk-KZ"`, `"ko-KR"`, `"ku"`, `"ky-KG"`, `"la"`, `"lb-LU"`, `"lg"`, `"lij"`, `"ln-CD"`, `"lo-LA"`, `"lt-LT"`, `"luo-KE"`, `"lv-LV"`, `"mg"`, `"mi-NZ"`, `"mk-MK"`, `"mn-MN"`, `"ms-MY"`, `"mt-MT"`, `"nb-NO"`, `"nl-NL"`, `"nso-ZA"`, `"ny-MW"`, `"oc-FR"`, `"pl-PL"`, `"ps-AF"`, `"pt-BR"`, `"pt-PT"`, `"ro-RO"`, `"roh"`, `"ru-RU"`, `"rw-RW"`, `"sah"`, `"sk-SK"`, `"sl-SI"`, `"sm"`, `"sn-ZW"`, `"so-SO"`, `"sq-AL"`, `"sr-Latn-RS"`, `"sr-RS"`, `"srd"`, `"ss"`, `"su-ID"`, `"sv-SE"`, `"sw-KE"`, `"sw-TZ"`, `"tg-TJ"`, `"th-TH"`, `"tk"`, `"tn"`, `"tok"`, `"ton"`, `"tr-TR"`, `"ts-ZA"`, `"tt"`, `"uk-UA"`, `"umb-AO"`, `"ur-IN"`, `"ur-PK"`, `"uz-UZ"`, `"vi-VN"`, `"vro"`, `"wo-SN"`, `"xh-ZA"`, `"yi"`, `"yo-NG"`, `"yue-Hant-HK"`, `"zh"`, `"zh-HK"`, `"zh-TW"`, `"zu-ZA"`

- **`translation_language`** (`Enum`, _optional_):
  Translate the subtitles into this language. Omit to keep the original spoken language. If you also pass srt_content or srt_file_url, set `language` to its source language for the most reliable translation.
  - Options: `"ab"`, `"ace"`, `"ach"`, `"af-ZA"`, `"ak"`, `"alz"`, `"am-ET"`, `"ar-AE"`, `"ar-BH"`, `"ar-DZ"`, `"ar-EG"`, `"ar-IL"`, `"ar-IQ"`, `"ar-JO"`, `"ar-KW"`, `"ar-LB"`, `"ar-MA"`, `"ar-OM"`, `"ar-PS"`, `"ar-QA"`, `"ar-SA"`, `"ar-TN"`, `"awa"`, `"ay"`, `"az-AZ"`, `"ban"`, `"bbc"`, `"be-BY"`, `"bem"`, `"bew"`, `"bg-BG"`, `"bho"`, `"bik"`, `"bm"`, `"bs-BA"`, `"bts"`, `"btx"`, `"bua"`, `"ca-ES"`, `"ceb-PH"`, `"cgg"`, `"chm"`, `"ckb-IQ"`, `"cnh"`, `"co"`, `"crh"`, `"crs"`, `"cs-CZ"`, `"cv"`, `"cy-GB"`, `"da-DK"`, `"de-DE"`, `"din"`, `"doi"`, `"dov"`, `"dv"`, `"dz"`, `"ee"`, `"el-GR"`, `"en-AU"`, `"en-GB"`, `"en-IN"`, `"en-NZ"`, `"en-US"`, `"eo"`, `"es-AR"`, `"es-BO"`, `"es-CL"`, `"es-CO"`, `"es-CR"`, `"es-DO"`, `"es-EC"`, `"es-ES"`, `"es-GT"`, `"es-HN"`, `"es-MX"`, `"es-NI"`, `"es-PA"`, `"es-PE"`, `"es-PR"`, `"es-PY"`, `"es-SV"`, `"es-US"`, `"es-UY"`, `"es-VE"`, `"et-EE"`, `"eu-ES"`, `"fa-IR"`, `"ff"`, `"fi-FI"`, `"fil-PH"`, `"fj"`, `"fr-CA"`, `"fr-FR"`, `"fy"`, `"ga"`, `"gaa"`, `"gd"`, `"gl-ES"`, `"gn"`, `"gom"`, `"ha-NG"`, `"haw"`, `"he-IL"`, `"hil"`, `"hmn"`, `"hr-HR"`, `"hrx"`, `"ht"`, `"hu-HU"`, `"hy-AM"`, `"id-ID"`, `"ig"`, `"ilo"`, `"is-IS"`, `"it-IT"`, `"ja-JP"`, `"ja-Latn-JP"`, `"jv-ID"`, `"ka-GE"`, `"kk-KZ"`, `"ko-KR"`, `"kri"`, `"ktu"`, `"ku"`, `"ky-KG"`, `"la"`, `"lb-LU"`, `"lg"`, `"li"`, `"lij"`, `"lmo"`, `"ln-CD"`, `"lo-LA"`, `"lt-LT"`, `"ltg"`, `"luo-KE"`, `"lus"`, `"lv-LV"`, `"mai"`, `"mak"`, `"mg"`, `"mi-NZ"`, `"min"`, `"mk-MK"`, `"mn-MN"`, `"mni-Mtei"`, `"ms-Arab"`, `"ms-MY"`, `"mt-MT"`, `"nb-NO"`, `"new"`, `"nl-NL"`, `"nr"`, `"nso-ZA"`, `"nus"`, `"ny-MW"`, `"oc-FR"`, `"om"`, `"pag"`, `"pam"`, `"pap"`, `"pl-PL"`, `"ps-AF"`, `"pt-BR"`, `"pt-PT"`, `"qu"`, `"rn"`, `"ro-RO"`, `"rom"`, `"ru-RU"`, `"rw-RW"`, `"scn"`, `"sg"`, `"shn"`, `"sk-SK"`, `"sl-SI"`, `"sm"`, `"sn-ZW"`, `"so-SO"`, `"sq-AL"`, `"sr-Latn-RS"`, `"sr-RS"`, `"ss"`, `"st"`, `"su-ID"`, `"sv-SE"`, `"sw-KE"`, `"sw-TZ"`, `"szl"`, `"tet"`, `"tg-TJ"`, `"th-TH"`, `"ti"`, `"tk"`, `"tn"`, `"tr-TR"`, `"ts-ZA"`, `"tt"`, `"ug"`, `"uk-UA"`, `"ur-IN"`, `"ur-PK"`, `"uz-UZ"`, `"vi-VN"`, `"xh-ZA"`, `"yi"`, `"yo-NG"`, `"yua"`, `"yue-Hant-HK"`, `"zh"`, `"zh-HK"`, `"zh-TW"`, `"zu-ZA"`

- **`srt_file_url`** (`string`, _optional_):
  Upload or paste a URL to your .srt subtitles file. When provided, transcription is skipped.

- **`srt_content`** (`string`, _optional_):
  Paste raw SRT subtitle text. Alternative to srt_file_url. When provided, transcription is skipped.

- **`vocabulary`** (`list<VocabularyEntry>`, _optional_):
  Optional list of terms to help auto-transcription correctly recognise brand names and domain jargon that providers commonly mis-spell (e.g. "VEED" → "vid"). Ignored when srt_content / srt_file_url is set.
  - Array of VocabularyEntry
  - Examples: [{"word":"VEED","replaces":["vid","feed"]}]

- **`customization`** (`PresetCustomization`, _optional_):
  Optional preset overrides: vertical position, shadow intensity, and per-tier text styling (font, weight, hex colour) for each word-importance tier. Any omitted field keeps the preset's default.



**Required Parameters Example**:

```json
{
  "video_url": "https://v3b.fal.media/files/b/0a967ce5/iARc_J0kLN9OEmiXnxT3l_substyle-example-input.mp4",
  "preset": "glass"
}
```

**Full Example**:

```json
{
  "video_url": "https://v3b.fal.media/files/b/0a967ce5/iARc_J0kLN9OEmiXnxT3l_substyle-example-input.mp4",
  "preset": "glass",
  "vocabulary": [
    {
      "word": "VEED",
      "replaces": [
        "vid",
        "feed"
      ]
    }
  ]
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`File`, _required_):
  Rendered video with styled subtitles
  - Examples: {"content_type":"video/mp4","url":"https://v3b.fal.media/files/b/0a9a3949/c5_GsxsCQaMZ3z-g2ehs2_substyle-example-output-compilation-v3.mp4"}



**Example Response**:

```json
{
  "video": {
    "content_type": "video/mp4",
    "url": "https://v3b.fal.media/files/b/0a9a3949/c5_GsxsCQaMZ3z-g2ehs2_substyle-example-output-compilation-v3.mp4"
  }
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/veed/subtitles \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "video_url": "https://v3b.fal.media/files/b/0a967ce5/iARc_J0kLN9OEmiXnxT3l_substyle-example-input.mp4",
     "preset": "glass"
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
    "veed/subtitles",
    arguments={
        "video_url": "https://v3b.fal.media/files/b/0a967ce5/iARc_J0kLN9OEmiXnxT3l_substyle-example-input.mp4",
        "preset": "glass"
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

const result = await fal.subscribe("veed/subtitles", {
  input: {
    video_url: "https://v3b.fal.media/files/b/0a967ce5/iARc_J0kLN9OEmiXnxT3l_substyle-example-input.mp4",
    preset: "glass"
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

- [Model Playground](https://fal.ai/models/veed/subtitles)
- [API Documentation](https://fal.ai/models/veed/subtitles/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=veed/subtitles)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
