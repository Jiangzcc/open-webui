# Mirelo SFX V1.5

> Generate synced sounds for any video, and return it with its new sound track (like MMAudio)


## Overview

- **Endpoint**: `https://fal.run/mirelo-ai/sfx-v1.5/video-to-video`
- **Model ID**: `mirelo-ai/sfx-v1.5/video-to-video`
- **Category**: video-to-video
- **Kind**: inference
**Tags**: video-to-video, sfx



## Pricing

- **Price**: $0.01 per seconds

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`video_url`** (`string`, _required_):
  A video url that can accessed from the API to process and add sound effects
  - Examples: "https://di3otfzjg1gxa.cloudfront.net/battlefield_scene_silent.mp4"

- **`text_prompt`** (`string`, _optional_):
  Additional description to guide the model
  - Examples: ""

- **`num_samples`** (`integer`, _optional_):
  The number of samples to generate from the model Default value: `2`
  - Default: `2`
  - Range: `2` to `8`

- **`seed`** (`integer`, _optional_):
  The seed to use for the generation. If not provided, a random seed will be used Default value: `8069`
  - Default: `8069`

- **`duration`** (`float`, _optional_):
  The duration of the generated audio in seconds Default value: `10`
  - Default: `10`
  - Range: `1` to `10`

- **`start_offset`** (`float`, _optional_):
  The start offset in seconds to start the audio generation from
  - Default: `0`



**Required Parameters Example**:

```json
{
  "video_url": "https://di3otfzjg1gxa.cloudfront.net/battlefield_scene_silent.mp4"
}
```

**Full Example**:

```json
{
  "video_url": "https://di3otfzjg1gxa.cloudfront.net/battlefield_scene_silent.mp4",
  "text_prompt": "",
  "num_samples": 2,
  "seed": 8069,
  "duration": 10
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`list<Video-Output>`, _required_):
  The processed video with sound effects
  - Array of Video-Output
  - Examples: [{"file_name":"generated_output_1.mp4","content_type":"video/mp4","url":"https://di3otfzjg1gxa.cloudfront.net/battlefield_scene_output_1.mp4"},{"file_name":"generated_output_2.mp4","content_type":"video/mp4","url":"https://di3otfzjg1gxa.cloudfront.net/battlefield_scene_output_2.mp4"}]



**Example Response**:

```json
{
  "video": [
    {
      "file_name": "generated_output_1.mp4",
      "content_type": "video/mp4",
      "url": "https://di3otfzjg1gxa.cloudfront.net/battlefield_scene_output_1.mp4"
    },
    {
      "file_name": "generated_output_2.mp4",
      "content_type": "video/mp4",
      "url": "https://di3otfzjg1gxa.cloudfront.net/battlefield_scene_output_2.mp4"
    }
  ]
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/mirelo-ai/sfx-v1.5/video-to-video \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "video_url": "https://di3otfzjg1gxa.cloudfront.net/battlefield_scene_silent.mp4"
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
    "mirelo-ai/sfx-v1.5/video-to-video",
    arguments={
        "video_url": "https://di3otfzjg1gxa.cloudfront.net/battlefield_scene_silent.mp4"
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

const result = await fal.subscribe("mirelo-ai/sfx-v1.5/video-to-video", {
  input: {
    video_url: "https://di3otfzjg1gxa.cloudfront.net/battlefield_scene_silent.mp4"
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

- [Model Playground](https://fal.ai/models/mirelo-ai/sfx-v1.5/video-to-video)
- [API Documentation](https://fal.ai/models/mirelo-ai/sfx-v1.5/video-to-video/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=mirelo-ai/sfx-v1.5/video-to-video)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
