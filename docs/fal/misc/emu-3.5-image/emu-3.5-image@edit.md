# Emu 3.5 Image

> Edit images with a text prompt using Emu 3.5 Image


## Overview

- **Endpoint**: `https://fal.run/fal-ai/emu-3.5-image/edit-image`
- **Model ID**: `fal-ai/emu-3.5-image/edit-image`
- **Category**: image-to-image
- **Kind**: inference


## Pricing

Your request will cost **$0.15** for 480p or **$0.30** for 720p.

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _required_):
  The prompt to edit the image.
  - Examples: "Recreate this image in ukiyo-e style"

- **`resolution`** (`ResolutionEnum`, _optional_):
  The resolution of the output image. Default value: `"720p"`
  - Default: `"720p"`
  - Options: `"480p"`, `"720p"`

- **`aspect_ratio`** (`AspectRatioEnum`, _optional_):
  The aspect ratio of the output image. Default value: `"auto"`
  - Default: `"auto"`
  - Options: `"auto"`, `"21:9"`, `"16:9"`, `"4:3"`, `"3:2"`, `"1:1"`, `"2:3"`, `"3:4"`, `"9:16"`, `"9:21"`

- **`enable_safety_checker`** (`boolean`, _optional_):
  Whether to enable the safety checker. Default value: `true`
  - Default: `true`

- **`seed`** (`integer`, _optional_):
  The seed for the inference.

- **`output_format`** (`OutputFormatEnum`, _optional_):
  The format of the output image. Default value: `"png"`
  - Default: `"png"`
  - Options: `"jpeg"`, `"png"`, `"webp"`

- **`sync_mode`** (`boolean`, _optional_):
  Whether to return the image in sync mode.
  - Default: `false`

- **`image_url`** (`string`, _required_):
  The image to edit.
  - Examples: "https://v3b.fal.media/files/b/lion/iC4LKAESSVo4ug-XzmR11_e9cafdab-c8b4-4267-804e-230e3d0d0814.png"



**Required Parameters Example**:

```json
{
  "prompt": "Recreate this image in ukiyo-e style",
  "image_url": "https://v3b.fal.media/files/b/lion/iC4LKAESSVo4ug-XzmR11_e9cafdab-c8b4-4267-804e-230e3d0d0814.png"
}
```

**Full Example**:

```json
{
  "prompt": "Recreate this image in ukiyo-e style",
  "resolution": "720p",
  "aspect_ratio": "auto",
  "enable_safety_checker": true,
  "output_format": "png",
  "image_url": "https://v3b.fal.media/files/b/lion/iC4LKAESSVo4ug-XzmR11_e9cafdab-c8b4-4267-804e-230e3d0d0814.png"
}
```


### Output Schema

The API returns the following output format:

- **`images`** (`list<ImageFile>`, _required_):
  The edited image.
  - Array of ImageFile
  - Examples: [{"url":"https://v3b.fal.media/files/b/monkey/t4nYWb1Zk7Uc6x2nSLysb.jpg","file_name":"t4nYWb1Zk7Uc6x2nSLysb.jpg","content_type":"image/jpeg","height":1168,"width":784}]

- **`seed`** (`integer`, _required_):
  The seed for the inference.
  - Examples: 1021074961



**Example Response**:

```json
{
  "images": [
    {
      "url": "https://v3b.fal.media/files/b/monkey/t4nYWb1Zk7Uc6x2nSLysb.jpg",
      "file_name": "t4nYWb1Zk7Uc6x2nSLysb.jpg",
      "content_type": "image/jpeg",
      "height": 1168,
      "width": 784
    }
  ],
  "seed": 1021074961
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/emu-3.5-image/edit-image \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "Recreate this image in ukiyo-e style",
     "image_url": "https://v3b.fal.media/files/b/lion/iC4LKAESSVo4ug-XzmR11_e9cafdab-c8b4-4267-804e-230e3d0d0814.png"
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
    "fal-ai/emu-3.5-image/edit-image",
    arguments={
        "prompt": "Recreate this image in ukiyo-e style",
        "image_url": "https://v3b.fal.media/files/b/lion/iC4LKAESSVo4ug-XzmR11_e9cafdab-c8b4-4267-804e-230e3d0d0814.png"
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

const result = await fal.subscribe("fal-ai/emu-3.5-image/edit-image", {
  input: {
    prompt: "Recreate this image in ukiyo-e style",
    image_url: "https://v3b.fal.media/files/b/lion/iC4LKAESSVo4ug-XzmR11_e9cafdab-c8b4-4267-804e-230e3d0d0814.png"
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

- [Model Playground](https://fal.ai/models/fal-ai/emu-3.5-image/edit-image)
- [API Documentation](https://fal.ai/models/fal-ai/emu-3.5-image/edit-image/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/emu-3.5-image/edit-image)

### fal.ai Platform

- [Platform Documentation](https://docs.fal.ai)
- [Python Client](https://docs.fal.ai/clients/python)
- [JavaScript Client](https://docs.fal.ai/clients/javascript)
