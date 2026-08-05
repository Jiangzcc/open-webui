# Mirelo SFX1.6

> Generate synced sounds for any video, and return it with its new sound track (like MMAudio). Now up to 60 seconds!


## Overview

- **Endpoint**: `https://fal.run/mirelo-ai/sfx1.6/video-to-video`
- **Model ID**: `mirelo-ai/sfx1.6/video-to-video`
- **Category**: video-to-video
- **Kind**: inference
**Description**: Generate synced sounds for any video, and return it with its new sound track (like MMAudio). Now up to 60 seconds!

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
  Video URL to add SFX to.
  - Examples: "https://di3otfzjg1gxa.cloudfront.net/cute_spider_silent.mp4"

- **`text_prompt`** (`string`, _optional_):
  Optional text prompt guiding generation.

- **`duration`** (`float`, _optional_):
  Duration of the generated SFX in seconds. Values >10 use sliding-window extended generation. Default value: `10`
  - Default: `10`
  - Range: `1` to `60`

- **`num_samples`** (`integer`, _optional_):
  Number of variations to generate. Default value: `2`
  - Default: `2`
  - Range: `1` to `4`

- **`seed`** (`integer`, _optional_):
  Seed for generation. -1 or None for random.



**Required Parameters Example**:

```json
{
  "video_url": "https://di3otfzjg1gxa.cloudfront.net/cute_spider_silent.mp4"
}
```

**Full Example**:

```json
{
  "video_url": "https://di3otfzjg1gxa.cloudfront.net/cute_spider_silent.mp4",
  "duration": 10,
  "num_samples": 2
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`list<Video>`, _required_):
  The processed video with sound effects
  - Array of Video
  - Examples: [{"url":"https://di3otfzjg1gxa.cloudfront.net/cute_spider.mp4","content_type":"video/mp4","file_name":"generated_output_1.mp4"}]



**Example Response**:

```json
{
  "video": [
    {
      "url": "https://di3otfzjg1gxa.cloudfront.net/cute_spider.mp4",
      "content_type": "video/mp4",
      "file_name": "generated_output_1.mp4"
    }
  ]
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/mirelo-ai/sfx1.6/video-to-video \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "video_url": "https://di3otfzjg1gxa.cloudfront.net/cute_spider_silent.mp4"
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
    "mirelo-ai/sfx1.6/video-to-video",
    arguments={
        "video_url": "https://di3otfzjg1gxa.cloudfront.net/cute_spider_silent.mp4"
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

const result = await fal.subscribe("mirelo-ai/sfx1.6/video-to-video", {
  input: {
    video_url: "https://di3otfzjg1gxa.cloudfront.net/cute_spider_silent.mp4"
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

- [Model Playground](https://fal.ai/models/mirelo-ai/sfx1.6/video-to-video)
- [API Documentation](https://fal.ai/models/mirelo-ai/sfx1.6/video-to-video/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=mirelo-ai/sfx1.6/video-to-video)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
