# Heygen v5 Digital Twin

> Create natural HeyGen Avatar V digital twin videos from text or audio, with lip-sync, optional backgrounds, captions, and MP4/WebM output.


## Overview

- **Endpoint**: `https://fal.run/fal-ai/heygen/avatar5/digital-twin`
- **Model ID**: `fal-ai/heygen/avatar5/digital-twin`
- **Category**: text-to-video
- **Kind**: inference
**Tags**: avatar, digital-twin, talking-avatar, text-to-video, lip-sync, heygen, video-generation



## Pricing

$0.10  per second of generated output video. The charge is based on final output duration in seconds.

For more details, see [fal.ai pricing](https://fal.ai/pricing).

## API Information

This model can be used via our HTTP API or more conveniently via our client libraries.
See the input and output schema below, as well as the usage examples.


### Input Schema

The API accepts the following input parameters:


- **`avatar`** (`string`, _optional_):
  Name of the Avatar V-eligible avatar to use. Default value: `"Abigail Sofa Front"`
  - Default: `"Abigail Sofa Front"`
  - Examples: "Abigail Office Front", "Abigail Office Side", "Abigail Sofa Front", "Abigail Sofa Side", "Amelia Business Training Front 2", "Amelia Business Training Front", "Amelia Business Training Side 2", "Amelia Business Training Side", "Amelia Lounge Front 2", "Amelia Lounge Front", "Amelia Lounge Side 2", "Amelia Lounge Side", "Amelia Yoga Front 2", "Amelia Yoga Front", "Amelia Yoga Side 2", "Amelia Yoga Side", "Anja Office Front", "Anja Office Side ", "Anja Sofa Front", "Anja Sofa Side ", "Ann Doctor Sitting", "Ann Doctor Standing", "Ann Therapist", "Annie Bar Sitting Front", "Annie Bar Sitting Side", "Annie Bar Standing Front 2", "Annie Bar Standing Front 3", "Annie Bar Standing Front", "Annie Bar Standing Side 2", "Annie Bar Standing Side 3", "Annie Bar Standing Side", "Annie Business Casual Standing Front 2", "Annie Business Casual Standing Front", "Annie Business Casual Standing Side 2", "Annie Business Casual Standing Side", "Annie Casual Sitting Front 2", "Annie Casual Sitting Front", "Annie Casual Sitting Side 2", "Annie Casual Sitting Side", "Annie Casual Standing Front 2", "Annie Casual Standing Front", "Annie Casual Standing Side 2", "Annie Casual Standing Side", "Annie Desk Sitting Front 2", "Annie Desk Sitting Front", "Annie Desk Sitting Side 2", "Annie Desk Sitting Side", "Annie Lounge Standing Front", "Annie Lounge Standing Side", "Annie Office Sitting Front 2", "Annie Office Sitting Front", "Annie Office Sitting Side 2", "Annie Office Sitting Side", "Annie Office Standing Front", "Annie Office Standing Side", "Annie Sofa Sitting Front 3", "Annie Sofa Sitting Front", "Annie Sofa Sitting Side 2", "Annie Sofa Sitting Side 3", "Annie Sofa Sitting Side", "Annie Sofa Sitting Front 2", "Annie Studio Pink Sitting Front", "Annie Studio Pink Sitting Side", "Annie Studio Pink Standing Front", "Annie Studio Pink Standing Side", "Artur Office Front 2", "Artur Office Front", "Artur Office Side 2", "Artur Office Side", "Artur Sofa Casual Front 2", "Artur Sofa Casual Front", "Artur Sofa Casual Side 2", "Artur Sofa Causal Side", "Aubrey Sofa Side", "Aubrey Night Scene Front", "Aubrey Outdoor Sport Front", "Aubrey Outdoor Sport Side", "Aubrey Sofa Front", "Blanka Lounge Front", "Blanka Lounge Side", "Blanka Outdoor Business Front", "Blanka Outdoor Business Side", "Blanka Outdoor Reading Front", "Blanka Outdoor Reading Side", "Blanka Picnic Front", "Blanka Picnic Side", "Bojan Business Training Front 2", "Bojan Business Training Front", "Bojan Business Training Side 2", "Bojan Business Training Side", "Bojan Lounge Front 2", "Bojan Lounge Front", "Bojan Lounge Side 2", "Bojan Lounge Side", "Bojan Sport Front 2", "Bojan Sport Front", "Bojan Sport Side 2", "Bojan Sport Side", "Brandon Business Sitting Front", "Brandon Business Sitting Side", "Brandon Business Standing Front", "Brandon Business Standing Side", "Brandon Casual Sitting Front", "Brandon Casual Sitting Side", "Brandon Kitchen Standing Front", "Brandon Kitchen Standing Side", "Brandon Lobby Sitting Front", "Brandon Lobby Sitting Side", "Brandon Lobby Standing Front", "Brandon Lobby Standing Side", "Brandon Office Sitting Front", "Brandon Office Sitting Side", "Brandon Office Standing Front", "Brandon Office Standing Side", "Brandon Sofa Sitting Front", "Brandon Sofa Sitting Side", "Brent Office Front 2", "Brent Office Front", "Brent Office Side 2", "Brent Office Side", "Brent Sofa Front 2", "Brent Sofa Front", "Brent Sofa Side 2", "Brent Sofa Side", "Bryan Fitness Coach", "Bryan Tech Expert", "Caroline Business Sitting Front", "Caroline Business Sitting Side", "Caroline Business Standing Front", "Caroline Business Standing Side", "Caroline Casual Sitting Front", "Caroline Casual Sitting Side", "Caroline Kitchen Standing Front", "Caroline Kitchen Standing Side", "Caroline Lobby Sitting Front", "Caroline Lobby Sitting Side", "Caroline Lobby Standing Front", "Caroline Lobby Standing Side", "Caroline Office Sitting Front", "Caroline Office Sitting Side", "Caroline Office Standing Front", "Caroline Office Standing Side", "Caroline Sofa Sitting Front", "Caroline Sofa Sitting Side", "Chloe Lounge Front", "Chloe Lounge Side", "Chloe Outdoor Side", "Conrad House Front", "Conrad House Side", "Conrad Sofa Front", "Conrad Sofa Side", "Derya Indoor Front 2", "Derya Indoor Front", "Derya Indoor Side 2", "Derya Indoor Side", "Derya Office Front 2", "Derya Office Front", "Derya Office Side 2", "Derya Office Side", "Dexter Doctor Sitting", "Dexter Doctor Standing", "Dexter Lawyer", "Elenora Fitness Coach", "Elenora Fitness Coach 2", "Elenora Tech Expert", "Emanuel Office Front", "Emanuel Office Side", "Emanuel Sofa Front", "Emanuel Sofa Side", "Emilia Outdoor Business Front", "Emilia Outdoor Business Side", "Emilia Outdoor Yoga Front 2", "Emilia Outdoor Yoga Front", "Emilia Outdoor Yoga Side", "Emilia Picnic Front", "Emilia Picnic Side", "Edward", "Fernando Business Indoor Front", "Fernando Business Indoor Side", "Fernando OutdoorChair Front 2", "Fernando Outdoor Chair Front", "Fernando Outdoor Chair Side", "Fernando Outdoor Front", "Fernando Outdoor Side", "Fernando Outdoor Table Front", "Fernando Outdoor Table Side", "Gala Bedroom Front", "Gala Business Sofa Front 2", "Gala Business Sofa Front 3", "Gala Business Sofa Front", "Gala Business Sofa Side 2", "Gala Business Sofa Side 3", "Gala Business Sofa Side", "Gala Casual Sofa with iPad Front", "Gala Casual Sofa with iPad Side 2", "Gala Casual Sofa with iPad Side", "Gala Office Front", "Gala Office Side", "Gala Sofa Front 2", "Gala Sofa Front 3", "Gala Sofa Front", "Gala Sofa Side 2", "Gala Sofa Side 3", "Gala Sofa Side", "Georgia Casual Front", "Georgia Casual Side", "Georgia Office Front", "Georgia Office Side", "Gerardo Sofa Side", "Gerardo Indoor Front", "Gerardo Indoor Side", "Gerardo Night Scene Front 2", "Gerardo Night Scene Front", "Gerardo Outdoor Sport Front", "Gerardo Outdoor Sport Side", "Gerardo Sofa Front", "Giulia Office Front 2", "Giulia Office Front", "Giulia Office Side 2", "Giulia Office Side", "Giulia Sofa Front", "Giulia Sofa Side", "Giulia Sofa  Front 2", "Giulia Sofa  Side 3", "Ida Lounge Front 2", "Ida Lounge Front", "Ida Lounge Side 2", "Ida Lounge Side", "Ida Sofa Front 2", "Ida Sofa Front", "Ida Sofa Side 2", "Ida Sofa Side", "Jocelyn Office Front 2", "Jocelyn Office Front", "Jocelyn Office Side 2", "Jocelyn Office Side", "Jocelyn Sofa Front 2", "Jocelyn Sofa Front", "Jocelyn Sofa Side 2", "Jocelyn Sofa Side", "Joel Couch Front", "Joel Couch Side", "Joel Gym Front", "Joel Gym Side", "Joel Mountain Front", "Joel Mountain Side", "Jonas Gym Front 2", "Jonas Gym Front", "Jonas Gym Side 2", "Jonas Gym Side ", "June Office Front 2", "Juan Office Front", "Juan Office Side 2", "Juan Office Side", "Juan Sofa Front 2", "Juan Sofa Front", "Juan Sofa Side 2", "Juan Sofa Side", "Judita Yoga Front 2", "Judita Yoga Front", "Judita Yoga Side 2", "Judita Yoga Side", "Judy Doctor Sitting", "Judy Doctor Standing", "Judy Lawyer", "Judy Teacher Sitting", "Judy HR", "Judy Teacher Standing", "June HR", "June Office Front", "June Office Side 2", "June Office Side", "June Sofa Casual Front 2", "June Sofa Casual Front", "June Sofa Casual Side 2", "June Sofa Casual Side", "Kavya Indoor Front", "Kavya Indoor Side", "Kavya Outdoor Side", "Kavya Outdoor Sport Front", "Kavya Outdoor Sport Side", "Kavya Sofa Front", "Kavya Sofa Side", "Leos Office Front 2", "Leos Office Front", "Leos Office Side 2", "Leos Office Side", "Leos Sofa Front 2", "Leos Sofa Front", "Leos Sofa Side 2", "Leos Sofa Side", "Leszek Lounge Front", "Leszek Lounge Side", "Leszek Outdoor Business Front", "Leszek Outdoor Business Side", "Leszek Outdoor Casual Front", "Leszek Outdoor Casual Side", "Leszek Sofa Front", "Leszek Sofa Side", "Leah", "Martina Office Front 2", "Martina Office Front", "Martina Office Side 2", "Martina Office Side", "Martina Sofa Front 2", "Martina Sofa Front", "Martina Sofa Side 2", "Martina Sofa Side", "Masha Office Front 2", "Masha Office Front", "Masha Office Side 2", "Masha Office Side", "Masha Sofa Casual Front 2", "Masha Sofa Casual Front", "Masha Sofa Casual Side 2", "Masha Sofa Casual Side", "Matteo Office Front 2", "Matteo Office Front", "Matteo Office Side 2", "Matteo Office Side", "Matteo Sofa Front 2", "Matteo Sofa Front", "Matteo Sofa Side 2", "Matteo Sofa Side", "Max Indoor Front", "Max Indoor Side", "Max Outdoor Sport Front", "Max Outdoor Sport Side", "Milena Office Front 2", "Milena Office Front", "Milena Office Side 2", "Milena Office Side", "Milena Sofa Front 2", "Milena Sofa Front", "Milena Sofa Side 2", "Milena Sofa Side", "Miles Outdoor Front", "Miles Outdoor Side", "Miles Sofa Front 2", "Miles Sofa Front", "Miles Sofa Side 2", "Miles Sofa Side", "Mireia Business Indoor Front", "Mireia Business Indoor Side", "Mireia Outdoor Chair Front", "Mireia Outdoor Front", "Mireia Outdoor Side", "Mireia Outdoor Table Front", "Mireia Outdoor Table Side", "Miyu Office Front 2", "Miyu Office Front", "Miyu Office Side 2", "Miyu Office Side", "Miyu Sofa Business Front", "Miyu Sofa Business Side", "Miyu Sofa Casual Front 2", "Miyu Sofa Casual Front", "Miyu Sofa Casual Side 2 ", "Miyu Sofa Casual Side", "Noah Lobby Front 2", "Noah Lobby Front", "Noah Lobby Side 2", "Noah Lobby Side", "Noah Office Front 2", "Noah Office Front", "Noah Office Side 2", "Noah Office Side", "Noah Sofa Front 2", "Noah Sofa Front ", "Noah Sofa Side 2", "Noah Sofa Side", "Oxana Gym Front 2", "Oxana Gym Front", "Oxana Gym Side 2", "Oxana Gym Side", "Oxana Office Front 2", "Oxana Office Front", "Oxana Office Side 2", "Oxana Office Side", "Oxana Sofa Front 2", "Oxana Sofa Front", "Oxana Sofa Side 2", "Oxana Sofa Side", "Oxana Yoga Front 2", "Oxana Yoga Front", "Oxana Yoga Side 2", "Oxana Yoga Side", "Patrizio Business Training Front", "Patrizio Business Training Side", "Patrizio Office Front", "Patrizio Office Side 2", "Patrizio Office Side", "Patrizio Sofa Front", "Patrizio Sofa Side", "Piper Business Sofa Front", "Piper Business Sofa Side", "Piper Education Front", "Piper Education Side", "Rasmus Lounge Front 2", "Rasmus Lounge Front", "Rasmus Lounge Side 2", "Rasmus Lounge Side", "Rasmus Sofa Front 2", "Rasmus Sofa Front", "Rasmus Sofa Side 2", "Rasmus Sofa Side", "Raul Business Sofa Front 2", "Raul Business Sofa Front", "Raul Business Sofa Side 2", "Raul Business Sofa Side", "Raul Casual Sofa Front 2", "Raul Casual Sofa Front", "Raul Casual Sofa Side 2", "Raul Casual Sofa Side", "Raul Casual Sofa no iPad Front", "Raul Casual Sofa no iPad Side", "Raul Casual Sofa with iPad Front", "Raul Casual Sofa with iPad Side", "Raul Office Front 2", "Raul Office Front", "Raul Office Side", "Raul Sofa Front 2", "Raul Sofa Front", "Raul Sofa Side 2", "Raul Sofa Side", "Ren Office Front 2", "Ren Office Front", "Ren Office Side 2", "Ren Office Side", "Ren Sofa Business Front", "Ren Sofa Business Side", "Ren Sofa Casual Front 2", "Ren Sofa Casual Front", "Ren Sofa Casual Side 2 ", "Ren Sofa Casual Side", "Riley Casual Front", "Riley Casual Side", "Riley Office Front", "Riley Office Side", "Roman Outdoor Sport Front", "Roman Outdoor Sport Side", "Sabine Office Front 2", "Sabine Office Front", "Sabine Office Side", "Sabine Sofa Side", "Santa Fireplace Front", "Santa Fireplace Side", "Scarlett Couch Front 2", "Scarlett Couch Front", "Scarlett Couch Side 2", "Scarlett Couch Side", "Scarlett Fireplace Front", "Scarlett Fireplace Side", "Scarlett Hall Front", "Scarlett Hall Side", "Scarlett Yoga Front", "Scarlett Yoga Side", "Shawn Therapist", "Silas Customer Support", "Silas HR", "Silas Lounge Front", "Silas Lounge Side", "Silas Sofa Side 2", "Silas Sofa Side", "Teodor Office Front 2", "Teodor Office Front", "Teodor Office Side 2", "Teodor Office Side", "Teodor Sofa Front 2", "Teodor Sofa Front", "Teodor Sofa Side 2", "Teodor Sofa Side", "Timothy Casual Front", "Timothy Casual Side", "Timothy Office Front", "Timothy Office Side", "Veit Office Front", "Veit Office Side", "Veit Sofa Front", "Veit Sofa Side", "Vernon Office Front 2", "Vernon Office Front", "Vernon Office Side 2", "Vernon Office Side", "Verena Office Front", "Verena Office Side", "Verena Sofa Front", "Verena Sofa Side", "Vernon Lounge Front 2", "Vernon Lounge Side 2", "Vernon Lounge Side", "Vince Business Sofa Front", "Vince Business Training Front", "Vince Business Training Side 2", "Vince Business Training Side", "Vince Sofa Casual Front 2", "Vince Sofa Casual Front", "Vince Sofa Casual Side 2", "Vince Sofa Casual Side", "Matthew"

- **`prompt`** (`string`, _optional_):
  Text the avatar will speak. Required when ``audio_url`` is not provided.
  - Examples: "Hello and welcome to this demonstration of HeyGen Avatar V."

- **`voice`** (`string`, _optional_):
  Name of the text-to-speech voice to use for the avatar when ``audio_url`` is not provided. Default value: `"Warm Pro Narrator"`
  - Default: `"Warm Pro Narrator"`
  - Examples: "Warm Pro Narrator", "Chill Brian", "Ivy", "John Doe", "Monika Sogam", "Hope ", "Archer ", "Brittney", "Patrick", "David Castlemore", "Michael C", "Adam Stone ", "Juniper", "Cassidy ", "Jessica Anne Bogart", "Arabella", "Andrew", "Spuds Oxley ", "Grace Elder", "Helen", "Canyon Rivers", "Derya - Lifelike - Excited 🤩", "Mellow Marcus", "Jack Sterling - Broadcaster 🎙️", "Brenda - UGC - 1.mp4", "Reid", "Reagan", "Terry", "Jenny", "Radio Rick", "Denise", "Tim in car - Excited 🤩", "Iskander", "Thompson", "Delicate Daisy - Excited 🤩", "Kingston", "George UGC 1", "Bold Blake", "Jane", "Expressive Evan", "Marianne - IA", "Aaron", "Modern Recipe Host - Voice 1", "Willow", "Cute Chloe - Friendly 😊", "Rafael", "June - Lifelike", "Crisp Chloe", "Slick Simon", "Nassim - Informative", "Baritone Ben", "Maxwell", "Ellie Faye - Excited 🤩", "Milani", "Feisty Fiona - Excited 🤩", "Professor Dean", "Rose - UGC - 1.mp4", "Shona", "Hudson Wilder", "Ann - IA", "Alastair Kensington", "Oxley", "Christina", "Andrew Rizz ", "Peyton", "Gerardo - Outdoor", "Chloe - Lifelike", "Stephanie", "Anthony - IA", "Signal - Voice 1", "Luca", "Lisa - Voice 1", "T.W.Tucker", "Jack Sullivan - Serious 😐", "Winter", "Mireia - Lifelike", "Georgia", "Stella", "Masha - Lifelike", "Charming Charles - Friendly 😊", "Serenity", "Annie - Excited", "Ralph", "Bethany", "Dominic", "Mason Finn", "Leena", "Veteran Victor", "Tamara", "Nik Public", "Calm Chloe", "Sevik", "Reilly", "Raul", "Imposing Ian", "Relaxed Ray", "Dexter - Professional", "Relaxed Rick", "Edwin", "Rupert Blackwood", "Ginny", "Hope"

- **`audio_url`** (`string`, _optional_):
  HTTP(S) URL of an audio file for the avatar to lip-sync to. When provided, the avatar uses this audio instead of text-to-speech and ``prompt``/``voice`` are ignored.

- **`fit`** (`FitEnum`, _optional_):
  How the avatar fits within the output frame. 'contain' keeps the full avatar in view (may letterbox); 'cover' fills the frame (may crop). Default value: `"cover"`
  - Default: `"cover"`
  - Options: `"contain"`, `"cover"`

- **`remove_background`** (`boolean`, _optional_):
  Remove the avatar's background. Requires a matting-enabled avatar.
  - Default: `false`

- **`background`** (`AvatarVBackground`, _optional_):
  Optional background to composite behind the avatar. Ignored when ``output_format='webm'`` (webm output is transparent).

- **`watermark`** (`AvatarVWatermark`, _optional_):
  Optional watermark image to overlay on the output video.

- **`caption`** (`boolean`, _optional_):
  Generate a sidecar SRT caption file alongside the video.
  - Default: `false`

- **`output_format`** (`OutputFormatEnum`, _optional_):
  Output container format. 'webm' produces a transparent video (automatically removes the background) and ignores the ``background`` field. Default value: `"mp4"`
  - Default: `"mp4"`
  - Options: `"mp4"`, `"webm"`

- **`resolution`** (`ResolutionEnum`, _optional_):
  Output resolution preset. Default value: `"720p"`
  - Default: `"720p"`
  - Options: `"720p"`, `"1080p"`, `"4k"`

- **`aspect_ratio`** (`AspectRatioEnum`, _optional_):
  Aspect ratio of the output video. Supported values: '16:9', '9:16', '4:5', '5:4', '1:1', and 'auto'. 'auto' preserves the source aspect ratio when HeyGen can read it, falling back to '16:9' otherwise. Default value: `"16:9"`
  - Default: `"16:9"`
  - Options: `"16:9"`, `"9:16"`, `"4:5"`, `"5:4"`, `"1:1"`, `"auto"`



**Required Parameters Example**:

```json
{}
```

**Full Example**:

```json
{
  "avatar": "Abigail Office Front",
  "prompt": "Hello and welcome to this demonstration of HeyGen Avatar V.",
  "voice": "Warm Pro Narrator",
  "fit": "cover",
  "output_format": "mp4",
  "resolution": "720p",
  "aspect_ratio": "16:9"
}
```


### Output Schema

The API returns the following output format:

- **`video`** (`File`, _required_):
  The generated Avatar V video file.
  - Examples: {"url":"https://v3b.fal.media/files/b/0a900636/DUES0_z4i7FWnife02ieH_output.mp4"}

- **`caption_file`** (`File`, _optional_):
  Generated caption file (SRT) when ``caption=True`` and HeyGen returns one.



**Example Response**:

```json
{
  "video": {
    "url": "https://v3b.fal.media/files/b/0a900636/DUES0_z4i7FWnife02ieH_output.mp4"
  }
}
```


## Usage Examples

### cURL

```bash
curl --request POST \
  --url https://fal.run/fal-ai/heygen/avatar5/digital-twin \
  --header "Authorization: Key $FAL_KEY" \
  --header "Content-Type: application/json" \
  --data '{}'
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
    "fal-ai/heygen/avatar5/digital-twin",
    arguments={},
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

const result = await fal.subscribe("fal-ai/heygen/avatar5/digital-twin", {
  input: {},
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

- [Model Playground](https://fal.ai/models/fal-ai/heygen/avatar5/digital-twin)
- [API Documentation](https://fal.ai/models/fal-ai/heygen/avatar5/digital-twin/api)
- [OpenAPI Schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/heygen/avatar5/digital-twin)

### fal.ai Platform

- [Platform Documentation](https://fal.ai/docs/documentation)
- [Python Client](https://fal.ai/docs/api-reference/client-libraries/python)
- [JavaScript Client](https://fal.ai/docs/api-reference/client-libraries/javascript)
