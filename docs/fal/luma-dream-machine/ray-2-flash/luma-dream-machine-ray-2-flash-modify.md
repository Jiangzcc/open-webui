# Luma Ray 2 Flash Modify

> Ray2 Flash Modify is a video generative model capable of restyling or retexturing the entire shot, from turning live-action into CG or stylized animation, to changing wardrobe, props, or the overall aesthetic and swap environments or time periods, giving you control over background, location, or even weather.


## Overview

- **Endpoint**: `https://fal.run/fal-ai/luma-dream-machine/ray-2-flash/modify`
- **Model ID**: `fal-ai/luma-dream-machine/ray-2-flash/modify`
- **Category**: video-to-video
- **Kind**: inference
**Tags**: modify, restyle



## Pricing

- **Price**: $0.12 per seconds

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`video_url`** (`string`, _required_):
  URL of the input video to modify
  - Examples: "https://v3.fal.media/files/zebra/9aDde3Te2kuJYHdR0Kz8R_output.mp4"

- **`image_url`** (`string`, _optional_):
  Optional URL of the first frame image for modification
  - Examples: "https://fal.media/files/koala/Kv2821G03ggpKK2AiZX71_d5fa7bacf06049cfaeb9588f6003b6d5.jpg"

- **`prompt`** (`string`, _optional_):
  Instruction for modifying the video

- **`mode`** (`ModeEnum`, _optional_):
  Amount of modification to apply to the video, adhere_1 is the least amount of modification, reimagine_3 is the most Default value: `"flex_1"`
  - Default: `"flex_1"`
  - Options: `"adhere_1"`, `"adhere_2"`, `"adhere_3"`, `"flex_1"`, `"flex_2"`, `"flex_3"`, `"reimagine_1"`, `"reimagine_2"`, `"reimagine_3"`



**Required Parameters Example**:

```json
{
  "video_url": "https://v3.fal.media/files/zebra/9aDde3Te2kuJYHdR0Kz8R_output.mp4"
}
```

**Full Example**:

```json
{
  "video_url": "https://v3.fal.media/files/zebra/9aDde3Te2kuJYHdR0Kz8R_output.mp4",
  "image_url": "https://fal.media/files/koala/Kv2821G03ggpKK2AiZX71_d5fa7bacf06049cfaeb9588f6003b6d5.jpg",
  "mode": "flex_1"
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`File`, _required_):
  URL of the modified video
  - Examples: {"url":"https://v3.fal.media/files/lion/_2UO2QC26T_R8vKeVGAdX_output.mp4"}



**Example Response**:

```json
{
  "video": {
    "url": "https://v3.fal.media/files/lion/_2UO2QC26T_R8vKeVGAdX_output.mp4"
  }
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/luma-dream-machine/ray-2-flash/modify \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "video_url": "https://v3.fal.media/files/zebra/9aDde3Te2kuJYHdR0Kz8R_output.mp4"
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
    "fal-ai/luma-dream-machine/ray-2-flash/modify",
    arguments={
        "video_url": "https://v3.fal.media/files/zebra/9aDde3Te2kuJYHdR0Kz8R_output.mp4"
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

const result = await fal.subscribe("fal-ai/luma-dream-machine/ray-2-flash/modify", {
  input: {
    video_url: "https://v3.fal.media/files/zebra/9aDde3Te2kuJYHdR0Kz8R_output.mp4"
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

- [Model Playground](https://fal.ai/models/fal-ai/luma-dream-machine/ray-2-flash/modify)
- [API Documentation](https://fal.ai/models/fal-ai/luma-dream-machine/ray-2-flash/modify/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/luma-dream-machine/ray-2-flash/modify)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
