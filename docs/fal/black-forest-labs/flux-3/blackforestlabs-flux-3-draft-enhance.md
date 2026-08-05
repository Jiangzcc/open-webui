# Flux 3 Draft Enhance

> FLUX.3 is Black Forest Labs' frontier audio/video model. Re-render a previously generated draft at full quality — same seed, same motion, no re-planning.


## Overview

- **Endpoint**: `https://fal.run/blackforestlabs/flux-3/draft-enhance`
- **Model ID**: `blackforestlabs/flux-3/draft-enhance`
- **Category**: video-to-video
- **Kind**: inference
**Tags**: stylized, transform, lipsync



## Pricing

Your request will be charged at **0.29** $ per second of the enhanced video (full-quality 1080p render). Synchronized audio is included at no extra cost.

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`draft_cache_url`** (`string`, _required_):
  URL or data URI of the encrypted draft cache bundle to enhance.

- **`safety_tolerance`** (`integer`, _optional_):
  The safety tolerance level for the generated video. 0 is the strictest and 4 is the most permissive. Default value: `2`
  - Default: `2`
  - Range: `0` to `4`



**Required Parameters Example**:

```json
{
  "draft_cache_url": ""
}
```

**Full Example**:

```json
{
  "draft_cache_url": "",
  "safety_tolerance": 2
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`File`, _required_):
  The enhanced video.



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
  --url https://fal.run/blackforestlabs/flux-3/draft-enhance \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "draft_cache_url": ""
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
    "blackforestlabs/flux-3/draft-enhance",
    arguments={
        "draft_cache_url": ""
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

const result = await fal.subscribe("blackforestlabs/flux-3/draft-enhance", {
  input: {
    draft_cache_url: ""
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

- [Model Playground](https://fal.ai/models/blackforestlabs/flux-3/draft-enhance)
- [API Documentation](https://fal.ai/models/blackforestlabs/flux-3/draft-enhance/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=blackforestlabs/flux-3/draft-enhance)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
