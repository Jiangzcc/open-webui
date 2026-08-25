# PATINA

> Generate complete seamlessly tiling PBR materials including normal, roughness, basecolor, height and metalness maps up to 8K


## Overview

- **Endpoint**: `https://fal.run/fal-ai/patina/material`
- **Model ID**: `fal-ai/patina/material`
- **Category**: text-to-image
- **Kind**: inference
**Tags**: material, pbr, displacement, metalness, normal, roughness, basecolor, albedo, height, 



## Pricing

Your request will cost **$0.01** plus **$0.02** per megapixel plus **$0.01** per megapixel per map type. When using 2x upscaling, an additional **$0.004** per (pre-upscaling) megapixel per map will be charged, and when using 4x upscaling, an additional **$0.016** per (pre-upscaling) megapixel per map will be charged. For example, A 1024x1024 material with all 5 maps and no upscaling (1K) will cost **$0.08**, and a 2048x2048 material with all 5 maps and 4x upscaling (8K) will cost $0.61.

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _required_):
  The text prompt describing the material/texture to generate.
  - Examples: "mossy stone wall"

- **`image_size`** (`ImageSize | Enum`, _optional_):
  Output texture dimensions in pixels. Default value: `square_hd`
  - Default: `"square_hd"`
  - One of: ImageSize | Enum

- **`num_inference_steps`** (`integer`, _optional_):
  Number of denoising steps for texture generation. Default value: `8`
  - Default: `8`
  - Range: `1` to `8`

- **`seed`** (`integer`, _optional_):
  Random seed for reproducible generation.

- **`num_images`** (`integer`, _optional_):
  Number of texture images to generate. Default value: `1`
  - Default: `1`
  - Range: `1` to `4`

- **`enable_prompt_expansion`** (`boolean`, _optional_):
  Expand prompt with an LLM for richer detail. Adds ~0.0025 credits. Default value: `true`
  - Default: `true`

- **`enable_safety_checker`** (`boolean`, _optional_):
  Enable the safety checker for generated images. Default value: `true`
  - Default: `true`

- **`tiling_mode`** (`TilingModeEnum`, _optional_):
  Tiling direction: 'both' (omnidirectional), 'horizontal', or 'vertical'. Default value: `"both"`
  - Default: `"both"`
  - Options: `"both"`, `"horizontal"`, `"vertical"`

- **`tile_size`** (`integer`, _optional_):
  Tile size in latent space (64 = 512px, 128 = 1024px). Default value: `128`
  - Default: `128`
  - Range: `32` to `256`

- **`tile_stride`** (`integer`, _optional_):
  Tile stride in latent space. Default value: `64`
  - Default: `64`
  - Range: `16` to `128`

- **`image_url`** (`string`, _optional_):
  URL of an input image for image-to-image or inpainting. When provided without mask_url, performs image-to-image; with mask_url, performs inpainting.

- **`mask_url`** (`string`, _optional_):
  URL of a mask image for inpainting. White regions are regenerated, black regions are preserved. Requires image_url.

- **`strength`** (`float`, _optional_):
  How much to transform the input image. Only used when image_url is provided. Default value: `0.6`
  - Default: `0.6`

- **`maps`** (`list<Enum>`, _optional_):
  Which PBR maps to predict. Deselect all to skip PBR estimation entirely. Defaults to all five.
  - Default: `["basecolor","normal","roughness","metalness","height"]`
  - Array of Enum

- **`upscale_factor`** (`UpscaleFactorEnum`, _optional_):
  Upscale factor for predicted PBR maps via SeedVR seamless upscaling. 0 = no upscaling, 2 = 2× resolution, 4 = 4× resolution. The base texture image is not upscaled. Default value: `"0"`
  - Default: `0`
  - Options: `0`, `2`, `4`

- **`output_format`** (`OutputFormatEnum`, _optional_):
  Output image format for textures and PBR maps. Default value: `"png"`
  - Default: `"png"`
  - Options: `"jpeg"`, `"png"`, `"webp"`



**Required Parameters Example**:

```json
{
  "prompt": "mossy stone wall"
}
```

**Full Example**:

```json
{
  "prompt": "mossy stone wall",
  "image_size": "square_hd",
  "num_inference_steps": 8,
  "num_images": 1,
  "enable_prompt_expansion": true,
  "enable_safety_checker": true,
  "tiling_mode": "both",
  "tile_size": 128,
  "tile_stride": 64,
  "strength": 0.6,
  "maps": [
    "basecolor",
    "normal",
    "roughness",
    "metalness",
    "height"
  ],
  "output_format": "png"
}
```


### Output Schema

The API returns the following output format:

- **`images`** (`list<ImageFile | MapImageFile>`, _required_):
  Generated tileable texture image(s) from z-image and predicted PBR material maps from PATINA.
  - Array of ImageFile | MapImageFile
  - Examples: [{"url":"https://v3b.fal.media/files/b/0a95760d/dX7FhHPQ0TOIESx9CyFdw_lhjHZKSq.png"},{"map_type":"basecolor","url":"https://v3b.fal.media/files/b/0a957610/LdI7qAvd7sOGArS_nD1L4_sL2PbKYz.png"},{"map_type":"height","url":"https://v3b.fal.media/files/b/0a957610/AVQruI2Vtm7y-lRBVbr34_Xc9WmnMW.png"},{"map_type":"normal","url":"https://v3b.fal.media/files/b/0a957610/V4Xj_KI9I-a6b-UEfIgrO_gQY8TeTS.png"},{"map_type":"roughness","url":"https://v3b.fal.media/files/b/0a957610/Eij1cULDUCTFHrglS9hT0_LWz3ZVhI.png"},{"map_type":"metalness","url":"https://v3b.fal.media/files/b/0a957610/tDGew4uKe1yxZYOPVoDEV_fmcwUVeE.png"}]

- **`seed`** (`integer`, _required_):
  Seed used for texture generation.

- **`prompt`** (`string`, _required_):
  The prompt used for texture generation (possibly expanded).

- **`timings`** (`Timings`, _optional_):
  End-to-end timing breakdown (seconds).



**Example Response**:

```json
{
  "images": [
    {
      "url": "https://v3b.fal.media/files/b/0a95760d/dX7FhHPQ0TOIESx9CyFdw_lhjHZKSq.png"
    },
    {
      "map_type": "basecolor",
      "url": "https://v3b.fal.media/files/b/0a957610/LdI7qAvd7sOGArS_nD1L4_sL2PbKYz.png"
    },
    {
      "map_type": "height",
      "url": "https://v3b.fal.media/files/b/0a957610/AVQruI2Vtm7y-lRBVbr34_Xc9WmnMW.png"
    },
    {
      "map_type": "normal",
      "url": "https://v3b.fal.media/files/b/0a957610/V4Xj_KI9I-a6b-UEfIgrO_gQY8TeTS.png"
    },
    {
      "map_type": "roughness",
      "url": "https://v3b.fal.media/files/b/0a957610/Eij1cULDUCTFHrglS9hT0_LWz3ZVhI.png"
    },
    {
      "map_type": "metalness",
      "url": "https://v3b.fal.media/files/b/0a957610/tDGew4uKe1yxZYOPVoDEV_fmcwUVeE.png"
    }
  ],
  "prompt": ""
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/patina/material \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "mossy stone wall"
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
    "fal-ai/patina/material",
    arguments={
        "prompt": "mossy stone wall"
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

const result = await fal.subscribe("fal-ai/patina/material", {
  input: {
    prompt: "mossy stone wall"
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

- [Model Playground](https://fal.ai/models/fal-ai/patina/material)
- [API Documentation](https://fal.ai/models/fal-ai/patina/material/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/patina/material)

### fal.ai Platform

- [Platform Documentation](https://docs.fal.ai)
- [Python Client](https://docs.fal.ai/clients/python)
- [JavaScript Client](https://docs.fal.ai/clients/javascript)
