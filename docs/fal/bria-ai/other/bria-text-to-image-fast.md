# Bria Text-to-Image Fast

> Bria's Text-to-Image model with perfect harmony of latency and quality. Trained exclusively on licensed data for safe and risk-free commercial use. Available also as source code and weights. For access to weights: https://bria.ai/contact-us


## Overview

- **Endpoint**: `https://fal.run/fal-ai/bria/text-to-image/fast`
- **Model ID**: `fal-ai/bria/text-to-image/fast`
- **Category**: text-to-image
- **Kind**: inference
**Tags**: image generation



## Pricing

- **Price**: $0.028 per generations

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _required_):
  The prompt you would like to use to generate images.
  - Examples: "A lone figure stands on the edge of a serene cliff at sunset, gazing out over a vast, mystical valley. The figure is clad in flowing robes that ripple in the gentle breeze, silhouetted against the golden and lavender hues of the sky. Below, a cascading waterfall pours into a sparkling river winding through a forest of bioluminescent trees. The scene blends the awe of nature with a touch of otherworldly wonder, inviting reflection and imagination."

- **`negative_prompt`** (`string`, _optional_):
  The negative prompt you would like to use to generate images. Default value: `""`
  - Default: `""`

- **`num_images`** (`integer`, _optional_):
  How many images you would like to generate. When using any Guidance Method, Value is set to 1. Default value: `4`
  - Default: `4`
  - Range: `1` to `4`

- **`aspect_ratio`** (`AspectRatioEnum`, _optional_):
  The aspect ratio of the image. When a guidance method is being used, the aspect ratio is defined by the guidance image and this parameter is ignored. Default value: `"1:1"`
  - Default: `"1:1"`
  - Options: `"1:1"`, `"2:3"`, `"3:2"`, `"3:4"`, `"4:3"`, `"4:5"`, `"5:4"`, `"9:16"`, `"16:9"`

- **`seed`** (`integer`, _optional_):
  The same seed and the same prompt given to the same version of the model
  will output the same image every time.
  - Range: `0` to `2147483647`

- **`num_inference_steps`** (`integer`, _optional_):
  The number of iterations the model goes through to refine the generated image. This parameter is optional. Default value: `8`
  - Default: `8`
  - Range: `4` to `10`

- **`guidance_scale`** (`float`, _optional_):
  The CFG (Classifier Free Guidance) scale is a measure of how close you want
  the model to stick to your prompt when looking for a related image to show you. Default value: `5`
  - Default: `5`
  - Range: `0` to `20`

- **`prompt_enhancement`** (`boolean`, _optional_):
  When set to true, enhances the provided prompt by generating additional, more descriptive variations, resulting in more diverse and creative output images.
  - Default: `false`

- **`medium`** (`MediumEnum`, _optional_):
  Which medium should be included in your generated images. This parameter is optional.
  - Options: `"photography"`, `"art"`

- **`guidance`** (`list<GuidanceInput>`, _optional_):
  Guidance images to use for the generation. Up to 4 guidance methods can be combined during a single inference.
  - Default: `[]`
  - Array of GuidanceInput

- **`sync_mode`** (`boolean`, _optional_):
  If `True`, the media will be returned as a data URI and the output data won't be available in the request history.
  - Default: `false`



**Required Parameters Example**:

```json
{
  "prompt": "A lone figure stands on the edge of a serene cliff at sunset, gazing out over a vast, mystical valley. The figure is clad in flowing robes that ripple in the gentle breeze, silhouetted against the golden and lavender hues of the sky. Below, a cascading waterfall pours into a sparkling river winding through a forest of bioluminescent trees. The scene blends the awe of nature with a touch of otherworldly wonder, inviting reflection and imagination."
}
```

**Full Example**:

```json
{
  "prompt": "A lone figure stands on the edge of a serene cliff at sunset, gazing out over a vast, mystical valley. The figure is clad in flowing robes that ripple in the gentle breeze, silhouetted against the golden and lavender hues of the sky. Below, a cascading waterfall pours into a sparkling river winding through a forest of bioluminescent trees. The scene blends the awe of nature with a touch of otherworldly wonder, inviting reflection and imagination.",
  "num_images": 4,
  "aspect_ratio": "1:1",
  "num_inference_steps": 8,
  "guidance_scale": 5,
  "guidance": []
}
```


### Output Schema

The API returns the following output format:

- **`images`** (`list<Image>`, _required_):
  The generated images
  - Array of Image
  - Examples: [{"height":1536,"file_size":3731290,"content_type":"image/png","file_name":"257cf8e7bd3a47c2959396343d5b38cf.png","url":"https://v3.fal.media/files/tiger/48e63e0K6C9XQYBuomoU-_257cf8e7bd3a47c2959396343d5b38cf.png","width":1536}]

- **`seed`** (`integer`, _required_):
  Seed value used for generation.



**Example Response**:

```json
{
  "images": [
    {
      "height": 1536,
      "file_size": 3731290,
      "content_type": "image/png",
      "file_name": "257cf8e7bd3a47c2959396343d5b38cf.png",
      "url": "https://v3.fal.media/files/tiger/48e63e0K6C9XQYBuomoU-_257cf8e7bd3a47c2959396343d5b38cf.png",
      "width": 1536
    }
  ]
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/bria/text-to-image/fast \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "A lone figure stands on the edge of a serene cliff at sunset, gazing out over a vast, mystical valley. The figure is clad in flowing robes that ripple in the gentle breeze, silhouetted against the golden and lavender hues of the sky. Below, a cascading waterfall pours into a sparkling river winding through a forest of bioluminescent trees. The scene blends the awe of nature with a touch of otherworldly wonder, inviting reflection and imagination."
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
    "fal-ai/bria/text-to-image/fast",
    arguments={
        "prompt": "A lone figure stands on the edge of a serene cliff at sunset, gazing out over a vast, mystical valley. The figure is clad in flowing robes that ripple in the gentle breeze, silhouetted against the golden and lavender hues of the sky. Below, a cascading waterfall pours into a sparkling river winding through a forest of bioluminescent trees. The scene blends the awe of nature with a touch of otherworldly wonder, inviting reflection and imagination."
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

const result = await fal.subscribe("fal-ai/bria/text-to-image/fast", {
  input: {
    prompt: "A lone figure stands on the edge of a serene cliff at sunset, gazing out over a vast, mystical valley. The figure is clad in flowing robes that ripple in the gentle breeze, silhouetted against the golden and lavender hues of the sky. Below, a cascading waterfall pours into a sparkling river winding through a forest of bioluminescent trees. The scene blends the awe of nature with a touch of otherworldly wonder, inviting reflection and imagination."
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

- [Model Playground](https://fal.ai/models/fal-ai/bria/text-to-image/fast)
- [API Documentation](https://fal.ai/models/fal-ai/bria/text-to-image/fast/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/bria/text-to-image/fast)

### fal.ai Platform

- [Platform Documentation](https://docs.fal.ai)
- [Python Client](https://docs.fal.ai/clients/python)
- [JavaScript Client](https://docs.fal.ai/clients/javascript)
