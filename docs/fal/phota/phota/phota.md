# Phota Text to Image

> Phota's model empowers developers, photographers, and creators with personalized photograph generation and editing.


## Overview

- **Endpoint**: `https://fal.run/fal-ai/phota`
- **Model ID**: `fal-ai/phota`
- **Category**: text-to-image
- **Kind**: inference
**Tags**: stylized, transform, typography, phota



## Pricing

Your request will cost **$0.09** per 1K image and **$0.18** per 4K image. Each 1K image costs 1 unit, and each 4K generation costs 2 units, with each unit costing **$0.09**.

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _required_):
  Text description of the desired image. In case you wish to use specific profiles, refer to them as [[profile_id_1]], [[profile_id_2]], etc.
  - Examples: "Middle Eastern man in traditional clothing sitting in a cool tent in the desert with a laptop"

- **`num_images`** (`integer`, _optional_):
  Number of images to generate. Default value: `1`
  - Default: `1`
  - Range: `1` to `4`

- **`output_format`** (`OutputFormatEnum`, _optional_):
  The format of the generated image. Default value: `"jpeg"`
  - Default: `"jpeg"`
  - Options: `"jpeg"`, `"png"`

- **`sync_mode`** (`boolean`, _optional_):
  If `True`, the media will be returned as a data URI and the output data won't be available in the request history.
  - Default: `false`

- **`resolution`** (`ResolutionEnum`, _optional_):
  Resolution of the generated image. Default value: `"1K"`
  - Default: `"1K"`
  - Options: `"1K"`, `"4K"`

- **`aspect_ratio`** (`AspectRatioEnum`, _optional_):
  Aspect ratio of the generated image. Default value: `"auto"`
  - Default: `"auto"`
  - Options: `"auto"`, `"1:1"`, `"16:9"`, `"4:3"`, `"3:4"`, `"9:16"`



**Required Parameters Example**:

```json
{
  "prompt": "Middle Eastern man in traditional clothing sitting in a cool tent in the desert with a laptop"
}
```

**Full Example**:

```json
{
  "prompt": "Middle Eastern man in traditional clothing sitting in a cool tent in the desert with a laptop",
  "num_images": 1,
  "output_format": "jpeg",
  "resolution": "1K",
  "aspect_ratio": "auto"
}
```


### Output Schema

The API returns the following output format:

- **`images`** (`list<ImageFile>`, _required_):
  The URL of the generated image.
  - Array of ImageFile
  - Examples: [{"url":"https://v3b.fal.media/files/b/0a8b90b7/9avg_nKJmcVinjQHJR_Ja.jpg"}]



**Example Response**:

```json
{
  "images": [
    {
      "url": "https://v3b.fal.media/files/b/0a8b90b7/9avg_nKJmcVinjQHJR_Ja.jpg"
    }
  ]
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/phota \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "Middle Eastern man in traditional clothing sitting in a cool tent in the desert with a laptop"
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
    "fal-ai/phota",
    arguments={
        "prompt": "Middle Eastern man in traditional clothing sitting in a cool tent in the desert with a laptop"
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

const result = await fal.subscribe("fal-ai/phota", {
  input: {
    prompt: "Middle Eastern man in traditional clothing sitting in a cool tent in the desert with a laptop"
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

- [Model Playground](https://fal.ai/models/fal-ai/phota)
- [API Documentation](https://fal.ai/models/fal-ai/phota/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/phota)

### fal.ai Platform

- [Platform Documentation](https://docs.fal.ai)
- [Python Client](https://docs.fal.ai/clients/python)
- [JavaScript Client](https://docs.fal.ai/clients/javascript)
