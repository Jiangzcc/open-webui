# Happy Oyster

> Realtime interactive world model — generate a world from a prompt, then explore it or direct its story as live video.


## Overview

- **Endpoint**: `https://fal.run/alibaba/happy-oyster`
- **Model ID**: `alibaba/happy-oyster`
- **Category**: video-to-video
- **Kind**: inference
**Tags**: video, happy-oyster



## Pricing

- **Price**: $0 per compute seconds

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`mode`** (`ModeEnum`, _required_):
  Experience mode: `adventure` (explore/play) or `directing` (story).
  - Options: `"adventure"`, `"directing"`

- **`prompt`** (`string`, _optional_):
  Natural-language world description. Required for simple creation unless `upload_mode` is `scenario_role`.
  - Examples: "A detective adventure in a rainy cyberpunk city"

- **`event_style`** (`Enum`, _optional_):
  Event style for generated events.
  - Options: `"normal"`, `"dramatic"`

- **`ref_world_id`** (`string`, _optional_):
  Encrypted ID of a template world to derive this world from.

- **`sync`** (`boolean`, _optional_):
  When true the upstream build is awaited (up to ~120s) before returning; otherwise poll `/worlds/build-status`.
  - Default: `false`

- **`perspective`** (`Enum`, _optional_):
  Camera perspective. Required in adventure mode.
  - Options: `"first_person"`, `"third_person"`

- **`upload_mode`** (`Enum`, _optional_):
  Adventure creation sub-mode; default `first_frame`.
  - Options: `"first_frame"`, `"scenario_role"`

- **`scene_prompt`** (`string`, _optional_):
  Scene description (scenario_role).

- **`role_prompt`** (`string`, _optional_):
  Role description (scenario_role).

- **`scene_image_url`** (`string`, _optional_):
  Scene reference image URL (scenario_role).

- **`role_image_url`** (`string`, _optional_):
  Role reference image URL (scenario_role).

- **`resolution`** (`Enum`, _optional_):
  Video resolution. Required in directing mode.
  - Options: `"480p"`, `"720p"`

- **`layout`** (`Enum`, _optional_):
  Camera movement style (directing mode).
  - Options: `"Stable"`, `"Fast"`

- **`narrative`** (`Enum`, _optional_):
  Narrative style (directing mode).
  - Options: `"Calm"`, `"Dramatic"`, `"Normal"`

- **`script_list`** (`object`, _optional_):
  Structured script (`subjects` + up to 45 `acts`); selects scriptlist creation. Directing mode only.

- **`first_frame_image_url`** (`string`, _optional_):
  First-frame anchor image URL.

- **`image_urls`** (`list<string>`, _optional_):
  Additional reference image URLs.
  - Array of string



**Required Parameters Example**:

```json
{
  "mode": "adventure"
}
```

**Full Example**:

```json
{
  "mode": "adventure",
  "prompt": "A detective adventure in a rainy cyberpunk city"
}
```


### Output Schema

The API returns the following output format:

- **`encrypted_world_id`** (`string`, _required_)

- **`status`** (`string`, _required_):
  `generating`, `ready`, or `failed`.

- **`first_frame`** (`string`, _optional_):
  First-frame image URL once available.

- **`name`** (`string`, _optional_):
  World title once built.

- **`mode`** (`Enum`, _optional_)
  - Options: `"adventure"`, `"directing"`



**Example Response**:

```json
{
  "encrypted_world_id": "",
  "status": ""
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/alibaba/happy-oyster/worlds/create \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "mode": "adventure"
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
    "alibaba/happy-oyster/worlds/create",
    arguments={
        "mode": "adventure"
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

const result = await fal.subscribe("alibaba/happy-oyster/worlds/create", {
  input: {
    mode: "adventure"
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

- [Model Playground](https://fal.ai/models/alibaba/happy-oyster)
- [API Documentation](https://fal.ai/models/alibaba/happy-oyster/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=alibaba/happy-oyster)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
