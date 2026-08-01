# Ideogram V2A

> Generate high-quality images, posters, and logos with Ideogram V2A. Features exceptional typography handling and realistic outputs optimized for commercial and creative use.


## Overview

- **Endpoint**: `https://fal.run/fal-ai/ideogram/v2a`
- **Model ID**: `fal-ai/ideogram/v2a`
- **Category**: text-to-image
- **Kind**: inference
**Tags**: realism, typography



## Pricing

- **Price**: $0.04 per images

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _required_)
  - Examples: "A comic style illustration of a skeleton sitting on a toilet in a bathroom. The bathroom has a Halloween decoration with a pumpkin jack-o-lantern and bats flying around. There is a text above the skeleton that says \"Just Waiting for Halloween with Ideogram 2.0 at fal.ai\""

- **`aspect_ratio`** (`AspectRatioEnum`, _optional_):
  The aspect ratio of the generated image Default value: `"1:1"`
  - Default: `"1:1"`
  - Options: `"10:16"`, `"16:10"`, `"9:16"`, `"16:9"`, `"4:3"`, `"3:4"`, `"1:1"`, `"1:3"`, `"3:1"`, `"3:2"`, `"2:3"`

- **`expand_prompt`** (`boolean`, _optional_):
  Whether to expand the prompt with MagicPrompt functionality. Default value: `true`
  - Default: `true`

- **`seed`** (`integer`, _optional_):
  Seed for the random number generator

- **`style`** (`StyleEnum`, _optional_):
  The style of the generated image Default value: `"auto"`
  - Default: `"auto"`
  - Options: `"auto"`, `"general"`, `"realistic"`, `"design"`, `"render_3D"`, `"anime"`

- **`sync_mode`** (`boolean`, _optional_):
  If `True`, the media will be returned as a data URI and the output data won't be available in the request history.
  - Default: `false`



**Required Parameters Example**:

```json
{
  "prompt": "A comic style illustration of a skeleton sitting on a toilet in a bathroom. The bathroom has a Halloween decoration with a pumpkin jack-o-lantern and bats flying around. There is a text above the skeleton that says \"Just Waiting for Halloween with Ideogram 2.0 at fal.ai\""
}
```

**Full Example**:

```json
{
  "prompt": "A comic style illustration of a skeleton sitting on a toilet in a bathroom. The bathroom has a Halloween decoration with a pumpkin jack-o-lantern and bats flying around. There is a text above the skeleton that says \"Just Waiting for Halloween with Ideogram 2.0 at fal.ai\"",
  "aspect_ratio": "1:1",
  "expand_prompt": true,
  "style": "auto"
}
```


### Output Schema

The API returns the following output format:

- **`images`** (`list<File>`, _required_)
  - Array of File
  - Examples: [{"url":"https://fal.media/files/monkey/cNaoxPl0YAWYb-QVBvO9F_image.png"}]

- **`seed`** (`integer`, _required_):
  Seed used for the random number generator
  - Examples: 123456



**Example Response**:

```json
{
  "images": [
    {
      "url": "https://fal.media/files/monkey/cNaoxPl0YAWYb-QVBvO9F_image.png"
    }
  ],
  "seed": 123456
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/ideogram/v2a \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "A comic style illustration of a skeleton sitting on a toilet in a bathroom. The bathroom has a Halloween decoration with a pumpkin jack-o-lantern and bats flying around. There is a text above the skeleton that says \"Just Waiting for Halloween with Ideogram 2.0 at fal.ai\""
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
    "fal-ai/ideogram/v2a",
    arguments={
        "prompt": "A comic style illustration of a skeleton sitting on a toilet in a bathroom. The bathroom has a Halloween decoration with a pumpkin jack-o-lantern and bats flying around. There is a text above the skeleton that says \"Just Waiting for Halloween with Ideogram 2.0 at fal.ai\""
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

const result = await fal.subscribe("fal-ai/ideogram/v2a", {
  input: {
    prompt: "A comic style illustration of a skeleton sitting on a toilet in a bathroom. The bathroom has a Halloween decoration with a pumpkin jack-o-lantern and bats flying around. There is a text above the skeleton that says \"Just Waiting for Halloween with Ideogram 2.0 at fal.ai\""
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

- [Model Playground](https://fal.ai/models/fal-ai/ideogram/v2a)
- [API Documentation](https://fal.ai/models/fal-ai/ideogram/v2a/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/ideogram/v2a)

### fal.ai Platform

- [Platform Documentation](https://docs.fal.ai)
- [Python Client](https://docs.fal.ai/clients/python)
- [JavaScript Client](https://docs.fal.ai/clients/javascript)
