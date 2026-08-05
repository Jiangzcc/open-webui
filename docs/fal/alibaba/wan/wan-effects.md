# Wan Effects

> Wan Effects generates high-quality videos with popular effects from images


## Overview

- **Endpoint**: `https://fal.run/fal-ai/wan-effects`
- **Model ID**: `fal-ai/wan-effects`
- **Category**: image-to-video
- **Kind**: inference
**Tags**: motion, effects



## Pricing

- **Price**: $0.35 per videos

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`subject`** (`string`, _required_):
  The subject to insert into the predefined prompt template for the selected effect.
  - Examples: "a cute kitten", "Donald Trump", "a tank", "a ceramic vase"

- **`image_url`** (`string`, _required_):
  URL of the input image.
  - Examples: "https://storage.googleapis.com/falserverless/web-examples/wan-effects/cat.jpg", "https://storage.googleapis.com/falserverless/web-examples/wan-effects/man_1.png", "https://storage.googleapis.com/falserverless/web-examples/wan-effects/woman_2.png"

- **`effect_type`** (`EffectTypeEnum`, _optional_):
  The type of effect to apply to the video. Default value: `"cakeify"`
  - Default: `"cakeify"`
  - Options: `"squish"`, `"muscle"`, `"inflate"`, `"crush"`, `"rotate"`, `"gun-shooting"`, `"deflate"`, `"cakeify"`, `"hulk"`, `"baby"`, `"bride"`, `"classy"`, `"puppy"`, `"snow-white"`, `"disney-princess"`, `"mona-lisa"`, `"painting"`, `"pirate-captain"`, `"princess"`, `"jungle"`, `"samurai"`, `"vip"`, `"warrior"`, `"zen"`, `"assassin"`, `"timelapse"`, `"tsunami"`, `"fire"`, `"zoom-call"`, `"doom-fps"`, `"fus-ro-dah"`, `"hug-jesus"`, `"robot-face-reveal"`, `"super-saiyan"`, `"jumpscare"`, `"laughing"`, `"cartoon-jaw-drop"`, `"crying"`, `"kissing"`, `"angry-face"`, `"selfie-younger-self"`, `"animeify"`, `"blast"`

- **`num_frames`** (`integer`, _optional_):
  Number of frames to generate. Default value: `81`
  - Default: `81`
  - Range: `81` to `100`

- **`frames_per_second`** (`integer`, _optional_):
  Frames per second of the generated video. Default value: `16`
  - Default: `16`
  - Range: `5` to `24`

- **`seed`** (`integer`, _optional_):
  Random seed for reproducibility. If None, a random seed is chosen.

- **`aspect_ratio`** (`AspectRatioEnum`, _optional_):
  Aspect ratio of the output video. Default value: `"16:9"`
  - Default: `"16:9"`
  - Options: `"16:9"`, `"9:16"`, `"1:1"`

- **`num_inference_steps`** (`integer`, _optional_):
  Number of inference steps for sampling. Higher values give better quality but take longer. Default value: `30`
  - Default: `30`
  - Range: `2` to `40`

- **`lora_scale`** (`float`, _optional_):
  The scale of the LoRA weight. Used to adjust effect intensity. Default value: `1`
  - Default: `1`
  - Range: `0.1` to `2`

- **`turbo_mode`** (`boolean`, _optional_):
  Whether to use turbo mode. If True, the video will be generated faster but with lower quality.
  - Default: `false`



**Required Parameters Example**:

```json
{
  "subject": "a cute kitten",
  "image_url": "https://storage.googleapis.com/falserverless/web-examples/wan-effects/cat.jpg"
}
```

**Full Example**:

```json
{
  "subject": "a cute kitten",
  "image_url": "https://storage.googleapis.com/falserverless/web-examples/wan-effects/cat.jpg",
  "effect_type": "cakeify",
  "num_frames": 81,
  "frames_per_second": 16,
  "aspect_ratio": "16:9",
  "num_inference_steps": 30,
  "lora_scale": 1
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`File`, _required_):
  The generated video
  - Examples: {"url":"https://storage.googleapis.com/falserverless/web-examples/wan-effects/cat_video.mp4"}

- **`seed`** (`integer`, _required_)



**Example Response**:

```json
{
  "video": {
    "url": "https://storage.googleapis.com/falserverless/web-examples/wan-effects/cat_video.mp4"
  }
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/wan-effects \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "subject": "a cute kitten",
     "image_url": "https://storage.googleapis.com/falserverless/web-examples/wan-effects/cat.jpg"
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
    "fal-ai/wan-effects",
    arguments={
        "subject": "a cute kitten",
        "image_url": "https://storage.googleapis.com/falserverless/web-examples/wan-effects/cat.jpg"
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

const result = await fal.subscribe("fal-ai/wan-effects", {
  input: {
    subject: "a cute kitten",
    image_url: "https://storage.googleapis.com/falserverless/web-examples/wan-effects/cat.jpg"
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

- [Model Playground](https://fal.ai/models/fal-ai/wan-effects)
- [API Documentation](https://fal.ai/models/fal-ai/wan-effects/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/wan-effects)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
