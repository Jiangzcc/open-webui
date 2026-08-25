# Phota

> Phota's model enables personalized photo editing, preserving identity while erasing distractions seamlessly.


## Overview

- **Endpoint**: `https://fal.run/fal-ai/phota/edit`
- **Model ID**: `fal-ai/phota/edit`
- **Category**: image-to-image
- **Kind**: inference
**Tags**: edit, personalization, typography, phota



## Pricing

Your request will cost **$0.09** per 1K image and **$0.18** per 4K image. Each 1K image costs 1 unit, and each 4K image charges 2 units, with each unit costing **$0.09**.

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _required_):
  Text description of the desired image. To refer to specific profiles, use [[profile_id_1]], [[profile_id_2]], etc.
  - Examples: "Make this scene more realistic but still keep the game vibes"

- **`num_images`** (`integer`, _optional_):
  Number of images to generate. Default value: `1`
  - Default: `1`
  - Range: `1` to `4`

- **`profile_ids`** (`list<string>`, _optional_):
  List of profile IDs to use for the image generation. Profiles may be tagged in the prompt as @Profile1, @Profile2, etc.
  - Array of string

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

- **`image_urls`** (`list<string>`, _required_):
  List of URLs/ Base64 data URIs of the images to edit. At least one image is required; for pure text-to-image generation use the `/` endpoint instead. A maximum of 10 images are supported, additional images will be ignored.
  - Array of string
  - Examples: ["https://v3b.fal.media/files/b/0a8b911d/Abk8vStrvmSPlzUqI_NN3_image_043.png"]



**Required Parameters Example**:

```json
{
  "prompt": "Make this scene more realistic but still keep the game vibes",
  "image_urls": [
    "https://v3b.fal.media/files/b/0a8b911d/Abk8vStrvmSPlzUqI_NN3_image_043.png"
  ]
}
```

**Full Example**:

```json
{
  "prompt": "Make this scene more realistic but still keep the game vibes",
  "num_images": 1,
  "output_format": "jpeg",
  "resolution": "1K",
  "aspect_ratio": "auto",
  "image_urls": [
    "https://v3b.fal.media/files/b/0a8b911d/Abk8vStrvmSPlzUqI_NN3_image_043.png"
  ]
}
```


### Output Schema

The API returns the following output format:

- **`images`** (`list<ImageFile>`, _required_):
  The URL of the edited image.
  - Array of ImageFile
  - Examples: [{"url":"https://v3b.fal.media/files/b/0a8b911d/XMqiVoO2ECXUZEUYmPl2l.jpg"}]



**Example Response**:

```json
{
  "images": [
    {
      "url": "https://v3b.fal.media/files/b/0a8b911d/XMqiVoO2ECXUZEUYmPl2l.jpg"
    }
  ]
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/phota/edit \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "Make this scene more realistic but still keep the game vibes",
     "image_urls": [
       "https://v3b.fal.media/files/b/0a8b911d/Abk8vStrvmSPlzUqI_NN3_image_043.png"
     ]
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
    "fal-ai/phota/edit",
    arguments={
        "prompt": "Make this scene more realistic but still keep the game vibes",
        "image_urls": ["https://v3b.fal.media/files/b/0a8b911d/Abk8vStrvmSPlzUqI_NN3_image_043.png"]
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

const result = await fal.subscribe("fal-ai/phota/edit", {
  input: {
    prompt: "Make this scene more realistic but still keep the game vibes",
    image_urls: ["https://v3b.fal.media/files/b/0a8b911d/Abk8vStrvmSPlzUqI_NN3_image_043.png"]
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

- [Model Playground](https://fal.ai/models/fal-ai/phota/edit)
- [API Documentation](https://fal.ai/models/fal-ai/phota/edit/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/phota/edit)

### fal.ai Platform

- [Platform Documentation](https://docs.fal.ai)
- [Python Client](https://docs.fal.ai/clients/python)
- [JavaScript Client](https://docs.fal.ai/clients/javascript)
