# Emu 3.5 Image

> Generate images from text using Emu 3.5 Image


## Overview

- **Endpoint**: `https://fal.run/fal-ai/emu-3.5-image/text-to-image`
- **Model ID**: `fal-ai/emu-3.5-image/text-to-image`
- **Category**: text-to-image
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
  The prompt to create the image.
  - Examples: "Capture an intimate close-up bathed in warm, soft, late-afternoon sunlight filtering into a quintessential 1960s kitchen. The focal point is a charmingly designed vintage package of all-purpose flour, resting invitingly on a speckled Formica countertop. The packaging itself evokes pure nostalgia: perhaps thick, slightly textured paper in a warm cream tone, adorned with simple, bold typography (a friendly serif or script) in classic red and blue \"ALL-PURPOSE FLOUR\", featuring a delightful illustration like a stylized sheaf of wheat or a cheerful baker character. In smaller bold print at the bottom of the package: \"NET WT 5 LBS (80 OZ) 2.27kg\". Focus sharply on the package details – the slightly soft edges of the paper bag, the texture of the vintage printing, the inviting \"All-Purpose Flour\" text. Subtle hints of the 1960s kitchen frame the shot – the chrome edge of the counter gleaming softly, a blurred glimpse of a pastel yellow ceramic tile backsplash, or the corner of a vintage metal canister set just out of focus. The shallow depth of field keeps attention locked on the beautifully designed package, creating an aesthetic rich in warmth, authenticity, and nostalgic appeal."

- **`resolution`** (`ResolutionEnum`, _optional_):
  The resolution of the output image. Default value: `"720p"`
  - Default: `"720p"`
  - Options: `"480p"`, `"720p"`

- **`aspect_ratio`** (`AspectRatioEnum`, _optional_):
  The aspect ratio of the output image. Default value: `"1:1"`
  - Default: `"1:1"`
  - Options: `"21:9"`, `"16:9"`, `"4:3"`, `"3:2"`, `"1:1"`, `"2:3"`, `"3:4"`, `"9:16"`, `"9:21"`

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



**Required Parameters Example**:

```json
{
  "prompt": "Capture an intimate close-up bathed in warm, soft, late-afternoon sunlight filtering into a quintessential 1960s kitchen. The focal point is a charmingly designed vintage package of all-purpose flour, resting invitingly on a speckled Formica countertop. The packaging itself evokes pure nostalgia: perhaps thick, slightly textured paper in a warm cream tone, adorned with simple, bold typography (a friendly serif or script) in classic red and blue \"ALL-PURPOSE FLOUR\", featuring a delightful illustration like a stylized sheaf of wheat or a cheerful baker character. In smaller bold print at the bottom of the package: \"NET WT 5 LBS (80 OZ) 2.27kg\". Focus sharply on the package details – the slightly soft edges of the paper bag, the texture of the vintage printing, the inviting \"All-Purpose Flour\" text. Subtle hints of the 1960s kitchen frame the shot – the chrome edge of the counter gleaming softly, a blurred glimpse of a pastel yellow ceramic tile backsplash, or the corner of a vintage metal canister set just out of focus. The shallow depth of field keeps attention locked on the beautifully designed package, creating an aesthetic rich in warmth, authenticity, and nostalgic appeal."
}
```

**Full Example**:

```json
{
  "prompt": "Capture an intimate close-up bathed in warm, soft, late-afternoon sunlight filtering into a quintessential 1960s kitchen. The focal point is a charmingly designed vintage package of all-purpose flour, resting invitingly on a speckled Formica countertop. The packaging itself evokes pure nostalgia: perhaps thick, slightly textured paper in a warm cream tone, adorned with simple, bold typography (a friendly serif or script) in classic red and blue \"ALL-PURPOSE FLOUR\", featuring a delightful illustration like a stylized sheaf of wheat or a cheerful baker character. In smaller bold print at the bottom of the package: \"NET WT 5 LBS (80 OZ) 2.27kg\". Focus sharply on the package details – the slightly soft edges of the paper bag, the texture of the vintage printing, the inviting \"All-Purpose Flour\" text. Subtle hints of the 1960s kitchen frame the shot – the chrome edge of the counter gleaming softly, a blurred glimpse of a pastel yellow ceramic tile backsplash, or the corner of a vintage metal canister set just out of focus. The shallow depth of field keeps attention locked on the beautifully designed package, creating an aesthetic rich in warmth, authenticity, and nostalgic appeal.",
  "resolution": "720p",
  "aspect_ratio": "1:1",
  "enable_safety_checker": true,
  "output_format": "png"
}
```


### Output Schema

The API returns the following output format:

- **`images`** (`list<ImageFile>`, _required_):
  The edited image.
  - Array of ImageFile
  - Examples: [{"url":"https://v3b.fal.media/files/b/koala/UFe9ES9IGdp0N90JmCyd4.jpg","file_name":"2_gRhwfsnmNKYtZ_dveyV.jpg","content_type":"image/jpeg","height":880,"width":1184}]

- **`seed`** (`integer`, _required_):
  The seed for the inference.
  - Examples: 1815037768



**Example Response**:

```json
{
  "images": [
    {
      "url": "https://v3b.fal.media/files/b/koala/UFe9ES9IGdp0N90JmCyd4.jpg",
      "file_name": "2_gRhwfsnmNKYtZ_dveyV.jpg",
      "content_type": "image/jpeg",
      "height": 880,
      "width": 1184
    }
  ],
  "seed": 1815037768
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/emu-3.5-image/text-to-image \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "Capture an intimate close-up bathed in warm, soft, late-afternoon sunlight filtering into a quintessential 1960s kitchen. The focal point is a charmingly designed vintage package of all-purpose flour, resting invitingly on a speckled Formica countertop. The packaging itself evokes pure nostalgia: perhaps thick, slightly textured paper in a warm cream tone, adorned with simple, bold typography (a friendly serif or script) in classic red and blue \"ALL-PURPOSE FLOUR\", featuring a delightful illustration like a stylized sheaf of wheat or a cheerful baker character. In smaller bold print at the bottom of the package: \"NET WT 5 LBS (80 OZ) 2.27kg\". Focus sharply on the package details – the slightly soft edges of the paper bag, the texture of the vintage printing, the inviting \"All-Purpose Flour\" text. Subtle hints of the 1960s kitchen frame the shot – the chrome edge of the counter gleaming softly, a blurred glimpse of a pastel yellow ceramic tile backsplash, or the corner of a vintage metal canister set just out of focus. The shallow depth of field keeps attention locked on the beautifully designed package, creating an aesthetic rich in warmth, authenticity, and nostalgic appeal."
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
    "fal-ai/emu-3.5-image/text-to-image",
    arguments={
        "prompt": "Capture an intimate close-up bathed in warm, soft, late-afternoon sunlight filtering into a quintessential 1960s kitchen. The focal point is a charmingly designed vintage package of all-purpose flour, resting invitingly on a speckled Formica countertop. The packaging itself evokes pure nostalgia: perhaps thick, slightly textured paper in a warm cream tone, adorned with simple, bold typography (a friendly serif or script) in classic red and blue \"ALL-PURPOSE FLOUR\", featuring a delightful illustration like a stylized sheaf of wheat or a cheerful baker character. In smaller bold print at the bottom of the package: \"NET WT 5 LBS (80 OZ) 2.27kg\". Focus sharply on the package details – the slightly soft edges of the paper bag, the texture of the vintage printing, the inviting \"All-Purpose Flour\" text. Subtle hints of the 1960s kitchen frame the shot – the chrome edge of the counter gleaming softly, a blurred glimpse of a pastel yellow ceramic tile backsplash, or the corner of a vintage metal canister set just out of focus. The shallow depth of field keeps attention locked on the beautifully designed package, creating an aesthetic rich in warmth, authenticity, and nostalgic appeal."
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

const result = await fal.subscribe("fal-ai/emu-3.5-image/text-to-image", {
  input: {
    prompt: "Capture an intimate close-up bathed in warm, soft, late-afternoon sunlight filtering into a quintessential 1960s kitchen. The focal point is a charmingly designed vintage package of all-purpose flour, resting invitingly on a speckled Formica countertop. The packaging itself evokes pure nostalgia: perhaps thick, slightly textured paper in a warm cream tone, adorned with simple, bold typography (a friendly serif or script) in classic red and blue \"ALL-PURPOSE FLOUR\", featuring a delightful illustration like a stylized sheaf of wheat or a cheerful baker character. In smaller bold print at the bottom of the package: \"NET WT 5 LBS (80 OZ) 2.27kg\". Focus sharply on the package details – the slightly soft edges of the paper bag, the texture of the vintage printing, the inviting \"All-Purpose Flour\" text. Subtle hints of the 1960s kitchen frame the shot – the chrome edge of the counter gleaming softly, a blurred glimpse of a pastel yellow ceramic tile backsplash, or the corner of a vintage metal canister set just out of focus. The shallow depth of field keeps attention locked on the beautifully designed package, creating an aesthetic rich in warmth, authenticity, and nostalgic appeal."
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

- [Model Playground](https://fal.ai/models/fal-ai/emu-3.5-image/text-to-image)
- [API Documentation](https://fal.ai/models/fal-ai/emu-3.5-image/text-to-image/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/emu-3.5-image/text-to-image)

### fal.ai Platform

- [Platform Documentation](https://docs.fal.ai)
- [Python Client](https://docs.fal.ai/clients/python)
- [JavaScript Client](https://docs.fal.ai/clients/javascript)
