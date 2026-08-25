# Heygen

> Use Heygen's Latest Model for Filler Word Removal.


## Overview

- **Endpoint**: `https://fal.run/fal-ai/heygen/v3/filler-word-removal`
- **Model ID**: `fal-ai/heygen/v3/filler-word-removal`
- **Category**: video-to-video
- **Kind**: inference
**Tags**: filler-word-removal



## Pricing

Your request will be charged at **0.01** $ per second of the input video, with a minimum charge for **60** seconds. Credits are not deducted if no cuts take place.

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`video_url`** (`string`, _required_):
  URL of the source video to remove filler words and long silences from.
  - Examples: "https://v3b.fal.media/files/b/0a9004c7/FM7Q5tK2b59x66Bl8HC0Z_vt-lang-en.mp4"

- **`title`** (`string`, _optional_):
  Optional display title for the removal job.



**Required Parameters Example**:

```json
{
  "video_url": "https://v3b.fal.media/files/b/0a9004c7/FM7Q5tK2b59x66Bl8HC0Z_vt-lang-en.mp4"
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`File`, _required_):
  The cleaned video file.

- **`original_duration`** (`float`, _required_):
  Duration of the source video in seconds.

- **`output_duration`** (`float`, _required_):
  Duration of the cleaned video in seconds.

- **`num_cuts`** (`integer`, _required_):
  Number of filler-word segments removed.

- **`reduction_pct`** (`float`, _required_):
  Percentage of the source duration removed.



**Example Response**:

```json
{
  "video": {
    "url": "",
    "content_type": "image/png",
    "file_name": "z9RV14K95DvU.png",
    "file_size": 4404019
  }
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/heygen/v3/filler-word-removal \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "video_url": "https://v3b.fal.media/files/b/0a9004c7/FM7Q5tK2b59x66Bl8HC0Z_vt-lang-en.mp4"
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
    "fal-ai/heygen/v3/filler-word-removal",
    arguments={
        "video_url": "https://v3b.fal.media/files/b/0a9004c7/FM7Q5tK2b59x66Bl8HC0Z_vt-lang-en.mp4"
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

const result = await fal.subscribe("fal-ai/heygen/v3/filler-word-removal", {
  input: {
    video_url: "https://v3b.fal.media/files/b/0a9004c7/FM7Q5tK2b59x66Bl8HC0Z_vt-lang-en.mp4"
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

- [Model Playground](https://fal.ai/models/fal-ai/heygen/v3/filler-word-removal)
- [API Documentation](https://fal.ai/models/fal-ai/heygen/v3/filler-word-removal/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/heygen/v3/filler-word-removal)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
