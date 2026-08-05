# Kling 1.0

> Generate video clips from your prompts using Kling 1.0


## Overview

- **Endpoint**: `https://fal.run/fal-ai/kling-video/v1/standard/effects`
- **Model ID**: `fal-ai/kling-video/v1/standard/effects`
- **Category**: text-to-video
- **Kind**: inference
**Tags**: motion



## Pricing

- **Price**: $0.045 per seconds

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`input_image_urls`** (`list<string>`, _optional_):
  URL of images to be used for hug, kiss or heart_gesture video.
  - Array of string
  - Examples: ["https://storage.googleapis.com/falserverless/juggernaut_examples/VHXMavzPyI27zi6JseyL4.png","https://storage.googleapis.com/falserverless/juggernaut_examples/QEW5VrzccxGva7mPfEXjf.png"]

- **`effect_scene`** (`EffectSceneEnum`, _required_):
  The effect scene to use for the video generation
  - Options: `"hug"`, `"kiss"`, `"heart_gesture"`, `"squish"`, `"expansion"`, `"fuzzyfuzzy"`, `"bloombloom"`, `"dizzydizzy"`, `"jelly_press"`, `"jelly_slice"`, `"jelly_squish"`, `"jelly_jiggle"`, `"pixelpixel"`, `"yearbook"`, `"instant_film"`, `"anime_figure"`, `"rocketrocket"`, `"fly_fly"`, `"disappear"`, `"lightning_power"`, `"bullet_time"`, `"bullet_time_360"`, `"media_interview"`, `"day_to_night"`, `"let's_ride"`, `"jumpdrop"`, `"swish_swish"`, `"running_man"`, `"jazz_jazz"`, `"swing_swing"`, `"skateskate"`, `"building_sweater"`, `"pure_white_wings"`, `"black_wings"`, `"golden_wing"`, `"pink_pink_wings"`, `"rampage_ape"`, `"a_list_look"`, `"countdown_teleport"`, `"firework_2026"`, `"instant_christmas"`, `"birthday_star"`, `"firework"`, `"celebration"`, `"tiger_hug_pro"`, `"pet_lion_pro"`, `"guardian_spirit"`, `"squeeze_scream"`, `"inner_voice"`, `"memory_alive"`, `"guess_what"`, `"eagle_snatch"`, `"hug_from_past"`, `"instant_kid"`, `"dollar_rain"`, `"cry_cry"`, `"building_collapse"`, `"mushroom"`, `"jesus_hug"`, `"shark_alert"`, `"lie_flat"`, `"polar_bear_hug"`, `"brown_bear_hug"`, `"office_escape_plow"`, `"watermelon_bomb"`, `"boss_coming"`, `"wig_out"`, `"car_explosion"`, `"tiger_hug"`, `"siblings"`, `"construction_worker"`, `"snatched"`, `"felt_felt"`, `"plushcut"`, `"drunk_dance"`, `"drunk_dance_pet"`, `"daoma_dance"`, `"bouncy_dance"`, `"smooth_sailing_dance"`, `"new_year_greeting"`, `"lion_dance"`, `"prosperity"`, `"great_success"`, `"golden_horse_fortune"`, `"red_packet_box"`, `"lucky_horse_year"`, `"lucky_red_packet"`, `"lucky_money_come"`, `"lion_dance_pet"`, `"dumpling_making_pet"`, `"fish_making_pet"`, `"pet_red_packet"`, `"lantern_glow"`, `"expression_challenge"`, `"overdrive"`, `"heart_gesture_dance"`, `"poping"`, `"martial_arts"`, `"running"`, `"nezha"`, `"motorcycle_dance"`, `"subject_3_dance"`, `"ghost_step_dance"`, `"phantom_jewel"`, `"zoom_out"`, `"cheers_2026"`, `"kiss_pro"`, `"fight_pro"`, `"hug_pro"`, `"heart_gesture_pro"`, `"dollar_rain_pro"`, `"pet_bee_pro"`, `"santa_random_surprise"`, `"magic_match_tree"`, `"happy_birthday"`, `"thumbs_up_pro"`, `"surprise_bouquet"`, `"bouquet_drop"`, `"3d_cartoon_1_pro"`, `"glamour_photo_shoot"`, `"box_of_joy"`, `"first_toast_of_the_year"`, `"my_santa_pic"`, `"santa_gift"`, `"steampunk_christmas"`, `"snowglobe"`, `"christmas_photo_shoot"`, `"ornament_crash"`, `"santa_express"`, `"particle_santa_surround"`, `"coronation_of_frost"`, `"spark_in_the_snow"`, `"scarlet_and_snow"`, `"cozy_toon_wrap"`, `"bullet_time_lite"`, `"magic_cloak"`, `"balloon_parade"`, `"jumping_ginger_joy"`, `"c4d_cartoon_pro"`, `"venomous_spider"`, `"throne_of_king"`, `"luminous_elf"`, `"woodland_elf"`, `"japanese_anime_1"`, `"american_comics"`, `"snowboarding"`, `"witch_transform"`, `"vampire_transform"`, `"pumpkin_head_transform"`, `"demon_transform"`, `"mummy_transform"`, `"zombie_transform"`, `"cute_pumpkin_transform"`, `"cute_ghost_transform"`, `"knock_knock_halloween"`, `"halloween_escape"`, `"baseball"`, `"korean_baseball"`, `"trampoline"`, `"trampoline_night"`, `"pucker_up"`, `"feed_mooncake"`, `"flyer"`, `"dishwasher"`, `"pet_chinese_opera"`, `"magic_fireball"`, `"gallery_ring"`, `"pet_moto_rider"`, `"muscle_pet"`, `"pet_delivery"`, `"mythic_style"`, `"steampunk"`, `"3d_cartoon_2"`, `"pet_chef"`, `"santa_gifts"`, `"santa_hug"`, `"girlfriend"`, `"boyfriend"`, `"heart_gesture_1"`, `"pet_wizard"`, `"smoke_smoke"`, `"gun_shot"`, `"double_gun"`, `"pet_warrior"`, `"long_hair"`, `"pet_dance"`, `"wool_curly"`, `"pet_bee"`, `"marry_me"`, `"piggy_morph"`, `"ski_ski"`, `"magic_broom"`, `"splashsplash"`, `"surfsurf"`, `"fairy_wing"`, `"angel_wing"`, `"dark_wing"`, `"emoji"`
  - Examples: "hug"

- **`duration`** (`DurationEnum`, _optional_):
  The duration of the generated video in seconds Default value: `"5"`
  - Default: `"5"`
  - Options: `"5"`, `"10"`



**Required Parameters Example**:

```json
{
  "effect_scene": "hug"
}
```

**Full Example**:

```json
{
  "input_image_urls": [
    "https://storage.googleapis.com/falserverless/juggernaut_examples/VHXMavzPyI27zi6JseyL4.png",
    "https://storage.googleapis.com/falserverless/juggernaut_examples/QEW5VrzccxGva7mPfEXjf.png"
  ],
  "effect_scene": "hug",
  "duration": "5"
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`File`, _required_):
  The generated video
  - Examples: {"file_name":"output.mp4","content_type":"video/mp4","url":"https://storage.googleapis.com/falserverless/kling/kling_ex.mp4.mp4"}



**Example Response**:

```json
{
  "video": {
    "file_name": "output.mp4",
    "content_type": "video/mp4",
    "url": "https://storage.googleapis.com/falserverless/kling/kling_ex.mp4.mp4"
  }
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/kling-video/v1/standard/effects \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{
     "effect_scene": "hug"
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
    "fal-ai/kling-video/v1/standard/effects",
    arguments={
        "effect_scene": "hug"
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

const result = await fal.subscribe("fal-ai/kling-video/v1/standard/effects", {
  input: {
    effect_scene: "hug"
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

- [Model Playground](https://fal.ai/models/fal-ai/kling-video/v1/standard/effects)
- [API Documentation](https://fal.ai/models/fal-ai/kling-video/v1/standard/effects/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/kling-video/v1/standard/effects)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
