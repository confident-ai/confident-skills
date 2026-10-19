# Images

Goldens, test cases, annotations and prompts can carry images. Put a `Media` where the
image belongs in any of their text fields: formatting it into a string leaves a
`[CONFIDENT:IMAGE:…]` marker, and the SDK sends the image with the request.
Only images are supported for now.

Never build `imagesMapping` yourself. The SDK fills it from the markers on every
request that accepts one. Each operation is shown for both Python and
TypeScript — use the code block matching your project.

## Create a Media

| Source | Python | TypeScript | What is sent |
| --- | --- | --- | --- |
| A public URL | `Media.from_url(url)` | `Media.fromUrl(url)` | the link |
| A local file | `Media.from_file(path)` | `Media.fromFile(path)` | the image, read when created |
| Bytes | `Media.from_bytes(data, "image/png")` | `Media.fromBytes(data, "image/png")` | the image |
| Base64 | `Media.from_base64(encoded, "image/png")` | `Media.fromBase64(encoded, "image/png")` | the image |

- The mime type is guessed from the extension for URLs and files, and is
  required for bytes and base64. It must be an `image/` type.
- `from_url` takes only `http(s)` URLs. Use `from_file` for a local path.
- `from_base64` takes the bare encoding, not a `data:` URI.
- A missing file or an invalid value raises where the `Media` is created, not
  when the request is sent.

## Put Images in Goldens

Format the `Media` into the text, inline or from a variable:

```python
from confident_ai import ConfidentAI, Media
from confident_ai.common import Turn, TurnRole
from confident_ai.datasets import MultiTurnGolden, SingleTurnGolden

client = ConfidentAI()

photo = Media.from_file("receipt.png")
client.datasets.push(
    alias="receipts",
    goldens=[SingleTurnGolden(input=f"What is the total? {photo}")],
)

client.datasets.push(
    alias="support-chats",
    goldens=[
        MultiTurnGolden(
            scenario="A customer sends a photo of a damaged parcel",
            turns=[
                Turn(
                    role=TurnRole.USER,
                    content=f"It arrived like this {Media.from_url('https://cdn.example.com/parcel.jpg')}",
                )
            ],
        )
    ],
)
```

```typescript
import { ConfidentAI, Media } from "confident-ai";
import { TurnRole } from "confident-ai/common";

const client = new ConfidentAI();

const photo = Media.fromFile("receipt.png");
await client.datasets.push("receipts", [
  { input: `What is the total? ${photo}` },
]);

await client.datasets.push("support-chats", [
  {
    scenario: "A customer sends a photo of a damaged parcel",
    turns: [
      {
        role: TurnRole.USER,
        content: `It arrived like this ${Media.fromUrl("https://cdn.example.com/parcel.jpg")}`,
      },
    ],
  },
]);
```

A marker inside a turn belongs to its golden, so a multi-turn golden carries the
images of all its turns.

The same works on every call that accepts images, and on the stateful handles
that delegate to them (`dataset.push()`, `dataset.create_golden()`, …):

- datasets: push, queue goldens, create and update a golden
- evaluations: `run_evals` / `runEvals`, per test case
- annotations: create and update, and annotating annotation queue items
- prompts: push, on a text prompt's `text` or a messages prompt's `content`

## Read Images Back

Pulled text carries its images as markers holding a signed link.
`parse_multimodal` (`parseMultimodal`) splits it into text and `Media` in
order, ready to map onto a model provider's content parts:

```python
from confident_ai import Media, parse_multimodal

dataset = client.dataset("<DATASET-ID>").pull()
for part in parse_multimodal(dataset.goldens[0].input):
    if isinstance(part, Media):
        print("image:", part.url)
    else:
        print("text:", part)
```

```typescript
import { Media, parseMultimodal } from "confident-ai";
import { SingleTurnGolden } from "confident-ai/datasets";

const dataset = await client.dataset("<DATASET-ID>").pull();
const golden = dataset.goldens![0] as SingleTurnGolden;
for (const part of parseMultimodal(golden.input)) {
  if (part instanceof Media) console.log("image:", part.url);
  else console.log("text:", part);
}
```

It takes one string; parse a list field item by item
(`[parse_multimodal(c) for c in golden.context]`). Markers it does not
recognise are left in the text.

Pushing a pulled golden back keeps its images, since its markers are sent by
reference.

## Things to Know

- **A local image only resolves in the process that made it.** Text saved to
  disk and pushed from another process sends a marker the server can't resolve.
  URL markers work anywhere.
- **Local images stay in memory** until the process exits.
- **An `imagesMapping` you set yourself wins** over the entries the SDK adds
  for the same marker.
- **The signed links in pulled text expire.** Fetch the image soon after
  pulling rather than storing the link.

## Next Steps

- Pull, edit and push datasets — `references/resources.md`.
- Configure a client and its keys — `references/quickstart.md`.
