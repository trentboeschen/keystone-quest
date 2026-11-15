---
name: write-adventure
description: Research and write a new Keystone Quest typing adventure as a validated adventures/<id>.json file. Use when asked to create, draft, generate or rework an adventure, scenario or story for the game (e.g. "make a Middle Ages adventure", "write one about the Apollo 13 rescue").
---

# Write a Keystone Quest adventure

Keystone Quest is a typing game for kids who like grown-up themes. Each adventure is a branching story set in a real historical moment. The player reads a short scene, then types one of the choices to decide what happens. Choices that match real history lead to the best endings, so reading carefully pays off. Each scene teaches one true fact (a "field note").

Follow every step. The validator at the end is not optional: the game silently misbehaves on files it would reject.

## 1. Pin down the brief

Settle these, from the request or by asking once:

- **Topic and moment:** one event over hours or days, not a whole era. "Escaping Pompeii, 24–25 August 79 CE" beats "Ancient Rome".
- **The player's role:** an ordinary person close to the action (an apprentice, a ship's boy, a junior assistant), not the famous figure.
- **What "doing well" means:** the decisions real people faced, where the historically sound choice is better. Examples: leaving early at Pompeii, recording before moving objects in Tutankhamun's tomb.

If the person gives only a topic, choose the rest yourself and say what you chose.

## 2. Research before writing

Every field note and every historical detail in a scene must be true. Use web search; don't write facts from memory.

- Search separately for each fact you plan to use. Prefer museums, universities, government heritage bodies, encyclopedias and primary sources over blogs.
- Note where historians disagree (dates, numbers) and say so in the fact itself ("usually dated…, but a 2018 find suggests…") rather than picking one silently.
- Use round, defensible numbers ("about 1,150", "more than 60").
- Collect 4–10 sources. They go in the file's `sources` field, so the parent can check them.
- Paraphrase. Never copy sentences from sources.

## 3. Design the story graph

Sketch scene names and links before writing prose. Target shape:

- **14–22 scenes**, one start scene.
- **3–5 endings:** at least one `good`, ideally one `mixed` and one `bad`. Endings are where the history lesson lands.
- **2–3 choices** in most scenes. A single choice ("type to continue") is fine for transitions, but no more than about a third of scenes.
- **Branches that rejoin.** Detours (a wrong guess, a delay) should cost something and then merge back. Don't build a tree that doubles every scene.
- **1–3 timed scenes** for genuinely urgent moments. Every timer needs a `timeout` scene, which is usually a setback, not death. Allow enough time to read and type at about 15 words per minute; the validator warns if a timer is too short.
- **Items:** use `gives` on one choice and `needs`/`lacks` on later choices to make earlier decisions matter (Pompeii's cushions, the tomb's careful records). Every item that's needed must be given somewhere.
- **No dead ends:** every combination of items a player can be carrying must leave at least one visible choice. The validator plays every path to check this.
- **Wrong choices teach.** When a choice goes against history, the next scene shows why, ideally with a character or the field note explaining what really happened.

## 4. Write the scenes

**Audience:** roughly ages 8–13, strong readers, who dislike "kiddie" games. Write like a good young-adult historical novel: concrete, sensory, serious, never cutesy. No jokes at history's expense.

**Story text (`text`):** 25–60 words, present tense, second person ("You…"). One clear situation that sets up the choices. Name real places, objects and people where accurate. Use a blank line (`\n\n`) for a paragraph break when needed.

**Field notes (`fact`):** one true, surprising fact of 15–40 words tied to that scene. Give most non-transition scenes one. No fact should repeat another.

**Choices (`text`), which the player types:**
- lowercase letters and spaces only; avoid punctuation and apostrophes ("dig under the huts", not "dig under the workmen's huts")
- 3–6 words, all choices in a scene within about 8 letters of each other in length, so the shortest isn't always the easy pick
- start each choice in a scene with a different word where possible, so the fade-out hint helps early
- never let one choice be the start of another ("run" and "run home")
- verb first, plain words a 9-year-old can spell
- the historically sound choice should not always come first

**Endings:** 30–60 words describing the outcome, plus a field note about the aftermath or how we know the history. Deaths are handled with restraint: state the outcome, no injury detail, no gore. Bad endings should feel earned and fair, never random.

**Accuracy pass:** reread every sentence and ask whether you could cite it. If not, cut it or label it as the story ("you are thirteen, apprenticed to a baker" is fine; an invented statistic is not).

## 5. Build the file

Save to `adventures/<id>.json`. The id is lowercase letters, numbers and dashes and must equal the file name (for example `adventures/apollo-13.json`). Write 2-space-indented JSON with keys in this order:

```json
{
  "id": "apollo-13",
  "title": "Apollo 13: Bring Them Home",
  "era": "Mission Control, Houston · 1970",
  "blurb": "One-line pitch for the adventure card, under 25 words.",
  "art": "none",
  "accent": "#2f5f9e",
  "published": false,
  "start": "start",
  "sources": [
    { "title": "Page or book title", "url": "https://..." }
  ],
  "scenes": {
    "start": {
      "text": "Story text.",
      "fact": "One true fact.",
      "choices": [
        { "text": "what the player types", "next": "scene-name" },
        { "text": "another choice here", "next": "other-scene", "gives": "item" }
      ]
    },
    "tense-moment": {
      "text": "...",
      "timer": 28,
      "timeout": "too-slow",
      "choices": [{ "text": "do the urgent thing", "next": "next-scene" }]
    },
    "best-ending": { "ending": "good", "text": "...", "fact": "...", "choices": [] }
  }
}
```

Field rules:
- `art`: `volcano`, `desert`, `castle`, `sea` or `none`. Pick the closest; `none` paints a plain band in the accent colour.
- `accent`: a `#rrggbb` colour that suits the subject and has enough contrast for white text.
- `published`: always `false`. The parent reviews and publishes it in the game's editor.
- Leave out `updated`; the server sets it.
- `ending`: `good`, `mixed` or `bad`. Ending scenes have `"choices": []`.
- `needs` / `lacks` / `gives`: comma-separated item names, lowercase.
- Scene names: short, descriptive, letters, numbers and dashes (`harbor`, `second-door`).

Study `adventures/pompeii.json` and `adventures/tomb.json` as finished examples of tone, length and structure.

## 6. Validate and fix

Run the validator from the repo root:

```
python3 .claude/skills/write-adventure/scripts/validate_adventure.py adventures/<id>.json
```

Fix every **error** and run it again until it says `OK`. Fix **warnings** too, unless you have a clear reason to keep one, such as two choices that deliberately start with "read it from…". Mention any warning you keep.

Then trace the best path and at least one bad path by hand, reading only the text and choices, as a player would. Check that the story makes sense, that the right choice is discoverable from what's on screen, and that no scene contradicts another.

## 7. Hand it over

Tell the person:
- the file path, and the adventure's title and one-line premise
- the scene count, the endings (good, mixed and bad, with their names) and the timed scenes
- any historical points where sources disagreed and how you handled them
- that it's saved with `"published": false`. They review it in the game's editor, then tick **Published**. If the repo is deployed by `git pull`, commit and push the file first.

Don't commit or push unless asked.
