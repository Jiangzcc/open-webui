# PATINA

> PATINA creates seamless high-resolution normal, roughness, basecolor (albedo), height (displacement) and metalness maps from images


## Overview

- **Endpoint**: `https://fal.run/fal-ai/patina`
- **Model ID**: `fal-ai/patina`
- **Category**: image-to-image
- **Kind**: inference
**Tags**: pbr, displacement, metalness, normal, roughness, basecolor, albedo, height, 



## Pricing

Your request will cost **$0.01** plus **$0.01** per megapixel, per output map. For example, a 1024x1024 input image generating all 5 map types will cost **$0.06**

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`image_url`** (`string`, _required_):
  URL of the input image (photograph or render).
  - Examples: "https://storage.googleapis.com/falserverless/gallery/patina-blog-hero-render.png"

- **`maps`** (`list<Enum>`, _optional_):
  Which PBR maps to predict. Defaults to all five.
  - Default: `["basecolor","normal","roughness","metalness","height"]`
  - Array of Enum

- **`seed`** (`integer`, _optional_):
  Random seed for reproducible denoising. If not set, a random seed is used.

- **`sync_mode`** (`boolean`, _optional_):
  If True, return images as data URIs instead of CDN URLs.
  - Default: `false`

- **`enable_safety_checker`** (`boolean`, _optional_):
  Enable the safety checker for images. Default value: `true`
  - Default: `true`

- **`output_format`** (`OutputFormatEnum`, _optional_):
  Output image format. Default value: `"png"`
  - Default: `"png"`
  - Options: `"jpeg"`, `"png"`, `"webp"`



**Required Parameters Example**:

```json
{
  "image_url": "https://storage.googleapis.com/falserverless/gallery/patina-blog-hero-render.png"
}
```

**Full Example**:

```json
{
  "image_url": "https://storage.googleapis.com/falserverless/gallery/patina-blog-hero-render.png",
  "maps": [
    "basecolor",
    "normal",
    "roughness",
    "metalness",
    "height"
  ],
  "enable_safety_checker": true,
  "output_format": "png"
}
```


### Output Schema

The API returns the following output format:

- **`images`** (`list<MapImageFile>`, _required_):
  Predicted PBR material maps.
  - Array of MapImageFile
  - Examples: [{"url":"https://storage.googleapis.com/falserverless/gallery/patina-blog-hero-basecolor.png","map_type":"basecolor"},{"url":"https://storage.googleapis.com/falserverless/gallery/patina-blog-hero-normal.png","map_type":"normal"},{"url":"https://storage.googleapis.com/falserverless/gallery/patina-blog-hero-roughness.png","map_type":"roughness"},{"url":"https://storage.googleapis.com/falserverless/gallery/patina-blog-hero-metalness.png","map_type":"metalness"},{"url":"https://storage.googleapis.com/falserverless/gallery/patina-blog-hero-height.png","map_type":"height"}]

- **`timings`** (`Timings`, _optional_):
  Timing breakdown (seconds).

- **`seed`** (`integer`, _required_):
  The seed used for denoising.



**Example Response**:

```json
{
  "images": [
    {
      "url": "https://storage.googleapis.com/falserverless/gallery/patina-blog-hero-basecolor.png",
      "map_type": "basecolor"
    },
    {
      "url": "https://storage.googleapis.com/falserverless/gallery/patina-blog-hero-normal.png",
      "map_type": "normal"
    },
    {
      "url": "https://storage.googleapis.com/falserverless/gallery/patina-blog-hero-roughness.png",
      "map_type": "roughness"
    },
    {
      "url": "https://storage.googleapis.com/falserverless/gallery/patina-blog-hero-metalness.png",
      "map_type": "metalness"
    },
    {
      "url": "https://storage.googleapis.com/falserverless/gallery/patina-blog-hero-height.png",
      "map_type": "height"
    }
  ]
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/patina \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "image_url": "https://storage.googleapis.com/falserverless/gallery/patina-blog-hero-render.png"
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
    "fal-ai/patina",
    arguments={
        "image_url": "https://storage.googleapis.com/falserverless/gallery/patina-blog-hero-render.png"
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

const result = await fal.subscribe("fal-ai/patina", {
  input: {
    image_url: "https://storage.googleapis.com/falserverless/gallery/patina-blog-hero-render.png"
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

- [Model Playground](https://fal.ai/models/fal-ai/patina)
- [API Documentation](https://fal.ai/models/fal-ai/patina/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/patina)

### fal.ai Platform

- [Platform Documentation](https://docs.fal.ai)
- [Python Client](https://docs.fal.ai/clients/python)
- [JavaScript Client](https://docs.fal.ai/clients/javascript)
