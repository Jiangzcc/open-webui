# Kling LipSync Text-to-Video

> Kling LipSync is a text-to-video model that generates realistic lip movements from text input.


## Overview

- **Endpoint**: `https://fal.run/fal-ai/kling-video/lipsync/text-to-video`
- **Model ID**: `fal-ai/kling-video/lipsync/text-to-video`
- **Category**: text-to-video
- **Kind**: inference
**Tags**: text to video, lipsync



## Pricing

Your request will be priced **$0.014** per input **video seconds**, rolling up to closest **5 second increment**. For example, if your video's duration is 3 seconds, it will be billed as a 5 second video

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`video_url`** (`string`, _required_):
  The URL of the video to generate the lip sync for. Supports .mp4/.mov, ≤100MB, 2-60s, 720p/1080p only, width/height 720–1920px. If validation fails, an error is returned.
  - Examples: "https://fal.media/files/koala/8teUPbRRMtAUTORDvqy0l.mp4"

- **`text`** (`string`, _required_):
  Text content for lip-sync video generation. Max 120 characters.
  - Examples: "Mental health is as important as physical health, shaping our emotions, thoughts, and daily interactions."

- **`voice_id`** (`VoiceIdEnum`, _required_):
  Voice ID to use for speech synthesis
  - Options: `"genshin_vindi2"`, `"zhinen_xuesheng"`, `"AOT"`, `"ai_shatang"`, `"genshin_klee2"`, `"genshin_kirara"`, `"ai_kaiya"`, `"oversea_male1"`, `"ai_chenjiahao_712"`, `"girlfriend_4_speech02"`, `"chat1_female_new-3"`, `"chat_0407_5-1"`, `"cartoon-boy-07"`, `"uk_boy1"`, `"cartoon-girl-01"`, `"PeppaPig_platform"`, `"ai_huangzhong_712"`, `"ai_huangyaoshi_712"`, `"ai_laoguowang_712"`, `"chengshu_jiejie"`, `"you_pingjing"`, `"calm_story1"`, `"uk_man2"`, `"laopopo_speech02"`, `"heainainai_speech02"`, `"reader_en_m-v1"`, `"commercial_lady_en_f-v1"`, `"tiyuxi_xuedi"`, `"tiexin_nanyou"`, `"girlfriend_1_speech02"`, `"girlfriend_2_speech02"`, `"zhuxi_speech02"`, `"uk_oldman3"`, `"dongbeilaotie_speech02"`, `"chongqingxiaohuo_speech02"`, `"chuanmeizi_speech02"`, `"chaoshandashu_speech02"`, `"ai_taiwan_man2_speech02"`, `"xianzhanggui_speech02"`, `"tianjinjiejie_speech02"`, `"diyinnansang_DB_CN_M_04-v2"`, `"yizhipiannan-v1"`, `"guanxiaofang-v2"`, `"tianmeixuemei-v1"`, `"daopianyansang-v1"`, `"mengwa-v1"`
  - Examples: "genshin_klee2"

- **`voice_language`** (`VoiceLanguageEnum`, _optional_):
  The voice language corresponding to the Voice ID Default value: `"en"`
  - Default: `"en"`
  - Options: `"zh"`, `"en"`

- **`voice_speed`** (`float`, _optional_):
  Speech rate for Text to Video generation Default value: `1`
  - Default: `1`
  - Range: `0.8` to `2`



**Required Parameters Example**:

```json
{
  "video_url": "https://fal.media/files/koala/8teUPbRRMtAUTORDvqy0l.mp4",
  "text": "Mental health is as important as physical health, shaping our emotions, thoughts, and daily interactions.",
  "voice_id": "genshin_klee2"
}
```

**Full Example**:

```json
{
  "video_url": "https://fal.media/files/koala/8teUPbRRMtAUTORDvqy0l.mp4",
  "text": "Mental health is as important as physical health, shaping our emotions, thoughts, and daily interactions.",
  "voice_id": "genshin_klee2",
  "voice_language": "en",
  "voice_speed": 1
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`File`, _required_):
  The generated video
  - Examples: {"url":"https://storage.googleapis.com/falserverless/kling/kling_text_lipsync.mp4"}



**Example Response**:

```json
{
  "video": {
    "url": "https://storage.googleapis.com/falserverless/kling/kling_text_lipsync.mp4"
  }
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/kling-video/lipsync/text-to-video \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "video_url": "https://fal.media/files/koala/8teUPbRRMtAUTORDvqy0l.mp4",
     "text": "Mental health is as important as physical health, shaping our emotions, thoughts, and daily interactions.",
     "voice_id": "genshin_klee2"
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
    "fal-ai/kling-video/lipsync/text-to-video",
    arguments={
        "video_url": "https://fal.media/files/koala/8teUPbRRMtAUTORDvqy0l.mp4",
        "text": "Mental health is as important as physical health, shaping our emotions, thoughts, and daily interactions.",
        "voice_id": "genshin_klee2"
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

const result = await fal.subscribe("fal-ai/kling-video/lipsync/text-to-video", {
  input: {
    video_url: "https://fal.media/files/koala/8teUPbRRMtAUTORDvqy0l.mp4",
    text: "Mental health is as important as physical health, shaping our emotions, thoughts, and daily interactions.",
    voice_id: "genshin_klee2"
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

- [Model Playground](https://fal.ai/models/fal-ai/kling-video/lipsync/text-to-video)
- [API Documentation](https://fal.ai/models/fal-ai/kling-video/lipsync/text-to-video/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/kling-video/lipsync/text-to-video)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
