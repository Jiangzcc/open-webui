# Bria's VRMBG 3.0 Realtime

> Remove video backgrounds in real time with Bria’s VRMBG 3.0 model. Built for live streaming, real-time video apps, content creation, and low-latency workflows that need fast, accurate background removal.


## Overview

- **Endpoint**: `https://fal.run/bria/video/background-removal/realtime`
- **Model ID**: `bria/video/background-removal/realtime`
- **Category**: video-to-video
- **Kind**: inference
**Tags**: bria, video, background-removal, realtime



## Pricing

Your request will cost **$0.0042** per second.

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`blur_strength`** (`integer`, _optional_):
  Background blur strength, 0-100 (used when background_type is 'blur'). Default value: `50`
  - Default: `50`
  - Range: `0` to `100`

- **`background_color`** (`BackgroundColorEnum`, _optional_):
  Solid background colour (used when background_type is 'color'). Default value: `"Black"`
  - Default: `"Black"`
  - Options: `"Black"`, `"White"`, `"Gray"`, `"Red"`, `"Green"`, `"Blue"`, `"Yellow"`, `"Cyan"`, `"Magenta"`, `"Orange"`

- **`background_type`** (`BackgroundTypeEnum`, _optional_):
  How to replace the background: 'color', 'image', or 'blur'. Default value: `"color"`
  - Default: `"color"`
  - Options: `"color"`, `"image"`, `"blur"`

- **`image_url`** (`string`, _optional_):
  Playground webcam/video source. Media is sent over WebRTC. Default value: `""`
  - Default: `""`

- **`background_image_url`** (`string`, _optional_):
  Background image URL or data URI (used when background_type is 'image'). Default value: `"null"`
  - Default: `null`



**Required Parameters Example**:

```json
{}
```

**Full Example**:

```json
{
  "blur_strength": 50,
  "background_color": "Black",
  "background_type": "color"
}
```


### Output Schema

The API returns the following output format:



**Example Response**:

```json
{}
```


## Usage Examples

### cURL

```bash
curl --request WEBSOCKET \
  --url https://fal.run/bria/video/background-removal/realtime \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{}'
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
    "bria/video/background-removal/realtime",
    arguments={},
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

const result = await fal.subscribe("bria/video/background-removal/realtime", {
  input: {},
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

- [Model Playground](https://fal.ai/models/bria/video/background-removal/realtime)
- [API Documentation](https://fal.ai/models/bria/video/background-removal/realtime/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=bria/video/background-removal/realtime)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
