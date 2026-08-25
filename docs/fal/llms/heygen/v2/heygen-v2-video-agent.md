# Heygen

> Heygen Text to Video Generation Model


## Overview

- **Endpoint**: `https://fal.run/fal-ai/heygen/v2/video-agent`
- **Model ID**: `fal-ai/heygen/v2/video-agent`
- **Category**: text-to-video
- **Kind**: inference
**Tags**: text-to-video



## Pricing

Your request will cost **$0.034** per output video second.

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`prompt`** (`string`, _required_):
  Natural language prompt describing the video to generate. Include details about style, visual elements, and desired length for best results.
  - Examples: "Create a 15-second explainer video about fal.ai Video Workflows.\n            Target audience: Developers, AI engineers, and creative tech teams\n            Brand colors: Teal, purple, and pink accents\n\n            Opening script:\n            \"Most video models just generate clips—but fal.ai powers your entire production pipeline.\"\n\n            Add animated text overlays highlighting:\n\n            Sub-second inference\n\n            Multi-model chaining (e.g., FLUX to Kling)\n\n            Custom LoRA integration\n\n            Production-ready API"

- **`config`** (`VideoAgentConfig`, _optional_):
  Video configuration options



**Required Parameters Example**:

```json
{
  "prompt": "Create a 15-second explainer video about fal.ai Video Workflows.\n            Target audience: Developers, AI engineers, and creative tech teams\n            Brand colors: Teal, purple, and pink accents\n\n            Opening script:\n            \"Most video models just generate clips—but fal.ai powers your entire production pipeline.\"\n\n            Add animated text overlays highlighting:\n\n            Sub-second inference\n\n            Multi-model chaining (e.g., FLUX to Kling)\n\n            Custom LoRA integration\n\n            Production-ready API"
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`File`, _required_):
  The generated video file
  - Examples: {"url":"https://v3b.fal.media/files/b/0a908e47/INRshxAq8GRlGCPo5txxU_output.mp4"}



**Example Response**:

```json
{
  "video": {
    "url": "https://v3b.fal.media/files/b/0a908e47/INRshxAq8GRlGCPo5txxU_output.mp4"
  }
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/heygen/v2/video-agent \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "prompt": "Create a 15-second explainer video about fal.ai Video Workflows.\n            Target audience: Developers, AI engineers, and creative tech teams\n            Brand colors: Teal, purple, and pink accents\n\n            Opening script:\n            \"Most video models just generate clips—but fal.ai powers your entire production pipeline.\"\n\n            Add animated text overlays highlighting:\n\n            Sub-second inference\n\n            Multi-model chaining (e.g., FLUX to Kling)\n\n            Custom LoRA integration\n\n            Production-ready API"
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
    "fal-ai/heygen/v2/video-agent",
    arguments={
        "prompt": "Create a 15-second explainer video about fal.ai Video Workflows.
                Target audience: Developers, AI engineers, and creative tech teams
                Brand colors: Teal, purple, and pink accents

                Opening script:
                \"Most video models just generate clips—but fal.ai powers your entire production pipeline.\"

                Add animated text overlays highlighting:

                Sub-second inference

                Multi-model chaining (e.g., FLUX to Kling)

                Custom LoRA integration

                Production-ready API"
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

const result = await fal.subscribe("fal-ai/heygen/v2/video-agent", {
  input: {
    prompt: "Create a 15-second explainer video about fal.ai Video Workflows.
              Target audience: Developers, AI engineers, and creative tech teams
              Brand colors: Teal, purple, and pink accents

              Opening script:
              \"Most video models just generate clips—but fal.ai powers your entire production pipeline.\"

              Add animated text overlays highlighting:

              Sub-second inference

              Multi-model chaining (e.g., FLUX to Kling)

              Custom LoRA integration

              Production-ready API"
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

- [Model Playground](https://fal.ai/models/fal-ai/heygen/v2/video-agent)
- [API Documentation](https://fal.ai/models/fal-ai/heygen/v2/video-agent/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/heygen/v2/video-agent)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
