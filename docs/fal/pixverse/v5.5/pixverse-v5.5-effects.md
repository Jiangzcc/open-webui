# PixVerse V5.5 Effects

> Pixverse Effects


## Overview

- **Endpoint**: `https://fal.run/fal-ai/pixverse/v5.5/effects`
- **Model ID**: `fal-ai/pixverse/v5.5/effects`
- **Category**: image-to-video
- **Kind**: inference


## Pricing

For a 5s video in single-clip mode without audio, your request will cost $0.15 for 360p and 540p, $0.2 for 720p, and $0.4 for 1080p. Enabling audio adds $0.05, and multi-clip mode adds $0.10 (or $0.15 with audio). For 8-second videos, costs double; for 10-second videos, costs are 2.2x the 5-second base (1080p not supported for 10s). For $1 you can run this model with approximately 2 times.



For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`effect`** (`EffectEnum`, _required_):
  The effect to apply to the video
  - Options: `"Kiss Me AI"`, `"Kiss"`, `"Muscle Surge"`, `"Warmth of Jesus"`, `"Anything, Robot"`, `"The Tiger Touch"`, `"Hug"`, `"Holy Wings"`, `"Microwave"`, `"Zombie Mode"`, `"Squid Game"`, `"Baby Face"`, `"Black Myth: Wukong"`, `"Long Hair Magic"`, `"Leggy Run"`, `"Fin-tastic Mermaid"`, `"Punch Face"`, `"Creepy Devil Smile"`, `"Thunder God"`, `"Eye Zoom Challenge"`, `"Who's Arrested?"`, `"Baby Arrived"`, `"Werewolf Rage"`, `"Bald Swipe"`, `"BOOM DROP"`, `"Huge Cutie"`, `"Liquid Metal"`, `"Sharksnap!"`, `"Dust Me Away"`, `"3D Figurine Factor"`, `"Bikini Up"`, `"My Girlfriends"`, `"My Boyfriends"`, `"Subject 3 Fever"`, `"Earth Zoom"`, `"Pole Dance"`, `"Vroom Dance"`, `"GhostFace Terror"`, `"Dragon Evoker"`, `"Skeletal Bae"`, `"Summoning succubus"`, `"Halloween Voodoo Doll"`, `"3D Naked-Eye AD"`, `"Package Explosion"`, `"Dishes Served"`, `"Ocean ad"`, `"Supermarket AD"`, `"Tree doll"`, `"Come Feel My Abs"`, `"The Bicep Flex"`, `"London Elite Vibe"`, `"Flora Nymph Gown"`, `"Christmas Costume"`, `"It's Snowy"`, `"Reindeer Cruiser"`, `"Snow Globe Maker"`, `"Pet Christmas Outfit"`, `"Adopt a Polar Pal"`, `"Cat Christmas Box"`, `"Starlight Gift Box"`, `"Xmas Poster"`, `"Pet Christmas Tree"`, `"City Santa Hat"`, `"Stocking Sweetie"`, `"Christmas Night"`, `"Xmas Front Page Karma"`, `"Grinch's Xmas Hijack"`, `"Giant Product"`, `"Truck Fashion Shoot"`, `"Beach AD"`, `"Shoal Surround"`, `"Mechanical Assembly"`, `"Lighting AD"`, `"Billboard AD"`, `"Product close-up"`, `"Parachute Delivery"`, `"Dreamlike Cloud"`, `"Macaron Machine"`, `"Poster AD"`, `"Truck AD"`, `"Graffiti AD"`, `"3D Figurine Factory"`, `"The Exclusive First Class"`, `"Art Zoom Challenge"`, `"I Quit"`, `"Hitchcock Dolly Zoom"`, `"Smell the Lens"`, `"I believe I can fly"`, `"Strikout Dance"`, `"Courtside Cam"`, `"Pit Crew Moment"`, `"K-Baseball Sprint"`, `"Toddler Doodle"`, `"Idol Ending"`, `"Apex Dance"`, `"OmniHero Forge"`, `"Palm Decode"`, `"The Age Ripple"`, `"My Future Is Limitless"`, `"Knee Slide"`, `"Epic Goal Save"`, `"Sideline Ball Boy"`, `"Cup Celebration"`, `"Victory Roar"`, `"Vuvuzela Fan"`, `"World Champion Lift"`, `"Tunnel to Captain"`, `"Liquid Soccer Morph"`, `"Jump Into Crowd 2"`, `"Golden Pitch Crasher"`, `"Stadium Fan Cam"`, `"Broadcast Moto GP"`, `"The Grotesque Clay"`, `"Rookie Star Card"`, `"The Final Hug"`, `"Sharp Post-Match Comment"`, `"Street Maverick"`, `"Pitch Legend"`, `"One Step At A Time"`, `"Birthday Mirror"`, `"Superstar Lobby"`, `"Final Battle Room"`, `"Top of the World"`, `"Mini Me Unboxed"`, `"WonderPOP Surprise"`, `"White Chicks"`, `"Kiss me"`, `"Pixel World"`, `"Mint in Box"`, `"Hands up, Hand"`, `"Flora Nymph Go"`, `"Somber Embrace"`, `"Beam me up"`, `"Suit Swagger"`

- **`image_url`** (`string`, _required_):
  Optional URL of the image to use as the first frame. If not provided, generates from text
  - Examples: "https://v3.fal.media/files/koala/q5ahL3KS7ikt3MvpNUG8l_image%20(72).webp"

- **`resolution`** (`ResolutionEnum`, _optional_):
  The resolution of the generated video. Default value: `"720p"`
  - Default: `"720p"`
  - Options: `"360p"`, `"540p"`, `"720p"`, `"1080p"`

- **`duration`** (`DurationEnum`, _optional_):
  The duration of the generated video in seconds Default value: `"5"`
  - Default: `"5"`
  - Options: `"5"`, `"8"`, `"10"`

- **`negative_prompt`** (`string`, _optional_):
  Negative prompt to be used for the generation. Limited to 2048 UTF-8 encoded bytes. Because the limit counts bytes rather than characters, emoji and non-Latin or accented characters (which use multiple bytes each) can push a visually short prompt over the cap. Default value: `""`
  - Default: `""`

- **`thinking_type`** (`Enum`, _optional_):
  Prompt optimization mode: 'enabled' to optimize, 'disabled' to turn off, 'auto' for model decision
  - Options: `"enabled"`, `"disabled"`, `"auto"`



**Required Parameters Example**:

```json
{
  "effect": "Kiss Me AI",
  "image_url": "https://v3.fal.media/files/koala/q5ahL3KS7ikt3MvpNUG8l_image%20(72).webp"
}
```

**Full Example**:

```json
{
  "effect": "Kiss Me AI",
  "image_url": "https://v3.fal.media/files/koala/q5ahL3KS7ikt3MvpNUG8l_image%20(72).webp",
  "resolution": "720p",
  "duration": "5"
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`File`, _required_):
  The generated video
  - Examples: {"file_size":3232402,"file_name":"output.mp4","content_type":"video/mp4","url":"https://fal.media/files/koala/awGY1lJd7lVsqQeSqjWqn_output.mp4"}



**Example Response**:

```json
{
  "video": {
    "file_size": 3232402,
    "file_name": "output.mp4",
    "content_type": "video/mp4",
    "url": "https://fal.media/files/koala/awGY1lJd7lVsqQeSqjWqn_output.mp4"
  }
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/pixverse/v5.5/effects \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "effect": "Kiss Me AI",
     "image_url": "https://v3.fal.media/files/koala/q5ahL3KS7ikt3MvpNUG8l_image%20(72).webp"
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
    "fal-ai/pixverse/v5.5/effects",
    arguments={
        "effect": "Kiss Me AI",
        "image_url": "https://v3.fal.media/files/koala/q5ahL3KS7ikt3MvpNUG8l_image%20(72).webp"
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

const result = await fal.subscribe("fal-ai/pixverse/v5.5/effects", {
  input: {
    effect: "Kiss Me AI",
    image_url: "https://v3.fal.media/files/koala/q5ahL3KS7ikt3MvpNUG8l_image%20(72).webp"
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

- [Model Playground](https://fal.ai/models/fal-ai/pixverse/v5.5/effects)
- [API Documentation](https://fal.ai/models/fal-ai/pixverse/v5.5/effects/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/pixverse/v5.5/effects)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
