# Keystone Quest

A typing game for kids: branching history adventures where you type your choices.

## What's in this folder

| File | What it does |
|---|---|
| `index.html` | The game and the adventure editor. |
| `api.php` | Reads and writes the adventure files. |
| `config.php-sample` | Template for your settings. Copy it to `config.php`. |
| `config.php` | Your editor password, backup count and whether players see their typing speed. You create it; git ignores it, so your password never gets committed. |
| `adventures/` | One `.json` file per adventure. The game loads every valid file in here; there is no manifest. |
| `Dockerfile`, `docker/`, `.dockerignore`, `render.yaml` | Run it in a container, set up for Render. |
| `.claude/skills/write-adventure/` | A Claude Code skill for researching and writing new adventures, with a validator. |
| `manifest.webmanifest`, `sw.js`, `icons/` | Make it installable as a home-screen app that works offline. |
| `.htaccess` | Sets the right file type for the app manifest, keeps the page and service worker fresh, and hides `.git` (Apache only). |
| `adventures/.htaccess` | Stops people downloading the files directly, so drafts stay hidden (Apache only). |

## Setup

1. Upload the whole folder to your server, for example to `/typing/`, or clone the repository there.
2. Copy `config.php-sample` to `config.php`, next to `api.php`, and change `EDIT_PASSWORD` from `change-me` to your own password:

   ```
   cp config.php-sample config.php
   ```
3. Make sure PHP can write to the `adventures/` folder. On most hosts that means permissions `775` (or `777` on some shared hosts) on `adventures/`.
4. Open the folder's URL in a browser. Click **Editor** and enter your password to create and edit adventures.

Settings in `config.php`:

| Setting | What it does |
|---|---|
| `EDIT_PASSWORD` | Password for creating and editing adventures. `''` turns editing off. |
| `BACKUPS_PER_ADVENTURE` | How many earlier versions of each adventure to keep. |
| `SHOW_TYPING_SPEED` | `true` shows words per minute to players; `false` hides it everywhere. Speed is still recorded in their data either way, so you can switch it back on later without losing anything. |

If you set up from an older `config.php` that lacks `SHOW_TYPING_SPEED`, speed is shown.

Until `config.php` exists, the game shows a setup message instead of the adventures.

Needs PHP 7.4 or newer. No database.

### Updating from git

Run `git pull` on the server. Your `config.php` and the `adventures/_backups/` folder are ignored by git, so pulling never overwrites them.

Adventures you create or edit on the server change files in `adventures/`. To keep them in the repository, commit them from the server, or download them with **Export** and commit them from your own computer. If you edit the same adventure in both places, `git pull` reports a conflict instead of silently replacing either version.

### If your server uses nginx instead of Apache

`.htaccess` is ignored, so add this to your site config to keep drafts private:

```
location ^~ /typing/adventures/ { deny all; }
location ~ /\.git { deny all; }
location ~ /typing/(index\.html|sw\.js|manifest\.webmanifest)$ { add_header Cache-Control "no-cache"; }
```

Also make sure your `mime.types` maps `webmanifest` to `application/manifest+json`. Adjust `/typing/` to wherever you put the game.

The home-screen app and offline play need HTTPS, which most hosts provide free through Let's Encrypt.

## Deploying on Render

Render has no built-in PHP support, so the game runs as a Docker service: PHP 8.3 with Apache, built from the `Dockerfile`.

**With the Blueprint (recommended):**
1. In the Render Dashboard choose **New → Blueprint** and pick this repository.
2. Enter an editor password when Render asks for `KQ_EDIT_PASSWORD`.
3. Render creates a **Starter** web service with a 1 GB persistent disk at `/var/data`, and redeploys on every push to `main`.

**By hand:** create a **Web Service** from the repo with the **Docker** runtime. Then:
- add a disk mounted at `/var/data`
- set the environment variables below

### Saved adventures need a disk

Render wipes a service's files on every deploy and restart. Adventures saved from the editor survive only on a persistent disk, and disks need a paid instance type such as Starter. On the free type the game runs, but editor changes vanish on the next deploy or spin-down. Free services also sleep when idle, so the first visit afterwards is slow.

On first start, the container copies the bundled adventures from `adventures/` onto the disk:
- Ones you've edited in the game are never overwritten.
- Ones you've deleted don't come back.
- A new adventure file pushed to the repo is copied over on the next deploy.

To change a bundled adventure that's already on the disk, edit it in the game, or use **Import** with the new file.

### Settings as environment variables

`config.php` isn't in the repo, so on Render the game reads its settings from environment variables. If both exist, `config.php` wins.

| Variable | Same as | Notes |
|---|---|---|
| `KQ_EDIT_PASSWORD` | `EDIT_PASSWORD` | Required for editing. Set it as a secret in Render. |
| `KQ_SHOW_TYPING_SPEED` | `SHOW_TYPING_SPEED` | `true` or `false`. |
| `KQ_BACKUPS_PER_ADVENTURE` | `BACKUPS_PER_ADVENTURE` | Defaults to 20. |
| `KQ_DATA_DIR` | — | Where adventure files and backups live. On Render, `/var/data/adventures`. It's outside the website folder, so drafts stay private. |

Render serves the site over HTTPS, so the home-screen app and offline play work there without extra setup.

### Running the container yourself

```
docker build -t keystone-quest .
docker run -p 8080:10000 -e KQ_EDIT_PASSWORD=change-me \
  -e KQ_DATA_DIR=/data/adventures -v keystone-data:/data keystone-quest
```

Then open http://localhost:8080.

## Adventure files

Each file in `adventures/` is one adventure. The file name is its id (`pompeii.json` → `pompeii`). Use lowercase letters, numbers and dashes.

```json
{
  "id": "pompeii",
  "title": "Escape from Pompeii",
  "era": "Bay of Naples · 79 CE",
  "blurb": "One-line pitch shown on the adventure card.",
  "art": "volcano",
  "accent": "#b8352a",
  "published": true,
  "updated": 1794774099061,
  "start": "start",
  "sources": [{ "title": "Where a fact came from", "url": "https://..." }],
  "scenes": {
    "start": {
      "text": "The story for this scene.",
      "fact": "Optional true fact the player collects as a field note.",
      "timer": 20,
      "timeout": "scene-if-time-runs-out",
      "choices": [
        { "text": "what the player types", "next": "another-scene", "needs": "", "lacks": "", "gives": "" }
      ]
    },
    "another-scene": { "ending": "good", "text": "An ending.", "choices": [] }
  }
}
```

**Listing info:** `title`, `era`, `blurb`, `art` (`volcano`, `desert`, `castle`, `sea` or `none`) and `accent` (card colour).

**`published`:** `true` shows the adventure to players. `false` makes it a draft that only signed-in editors can see.

**`updated`:** set by the server on every save. Leave it alone.

**`sources`:** optional list of references for the facts in the adventure. The game doesn't show them; they're for whoever reviews the adventure.

**Scenes:**
- `ending` is `good`, `mixed` or `bad`, or left out for a normal scene.
- `timer` (seconds) and `timeout` (scene to jump to) are optional.
- On a choice, `needs`, `lacks` and `gives` are comma-separated item names. Use them to show or hide choices based on what the player has picked up.

## Adding adventures

- **In the game:** sign in as editor, then use **New adventure**, **Duplicate** or **Import**. Saving writes straight to `adventures/`.
- **By hand:** drop a `.json` file into `adventures/`. It appears on the next page load. Turn on `published` when it's ready.

## Writing adventures with Claude

The repo includes a Claude Code skill, `write-adventure`. Open the repo in Claude Code and ask for an adventure, for example "write an adventure about the Apollo 13 rescue". Claude will:

1. research the history with web search and record its sources
2. design a story graph with several endings, a timed scene or two, and items that carry choices forward
3. write `adventures/<id>.json` as an unpublished draft
4. run the validator and fix anything it finds

Review the draft in the game's editor, then tick **Published**.

You can run the validator yourself on any adventure, including ones written by hand:

```
python3 .claude/skills/write-adventure/scripts/validate_adventure.py adventures/*.json
```

It plays every path through the story to make sure:

- no player can get stuck
- every ending can be reached
- no choice is the start of another one
- choices only use keys on the game's keyboard
- timers leave enough time for a beginner to read and type

## Safety nets

- Every save and delete first copies the old version to `adventures/_backups/`. The last 20 per adventure are kept; you can change that with `BACKUPS_PER_ADVENTURE` in `config.php`. To restore one, copy it back into `adventures/` with the original file name.
- If someone saves an adventure after you opened it (another tab, another person, or a hand edit on the server), the editor warns you. You can then choose to overwrite their version or load it.

## Difficulty

Each player picks a difficulty in their player panel. It scales every timed scene in every adventure:

| Setting | Timers |
|---|---|
| No timers | Timed scenes wait for you |
| Relaxed | 1.5× longer |
| Normal | As written in the adventure |
| Challenging | 0.7× (30% shorter) |
| Expert | 0.5× (half as long) |

Write adventure timers for Normal. The validator checks them against a beginner's typing speed. Each finished run records the difficulty it was played on.

## iPad and touchscreens

**With a keyboard** (Bluetooth or a keyboard case), the iPad works like a computer. This is the best way to practise.

**Without a keyboard,** tap **Tap to type** or anywhere on the scene to bring up the iPad's keyboard. While it's open, the game hides the picture and its drawn keyboard, and keeps the timer and choices just above the iPad keyboard. This works in portrait and landscape.

To keep practice honest with the on-screen keyboard:
- **Letter by letter only.** Autocorrect and auto-capitals are switched off. Word suggestions can't be hidden on iPad, so any whole word inserted at once is rejected with a message.
- **Separate records.** Each run records whether it was typed on a keyboard or the screen. Speed badges, overall typing speed and the trouble-key list only count keyboard typing, because screen typos aren't finger mistakes.
- **Relaxed tip.** In timed scenes, players on Normal or harder see a tip suggesting Relaxed difficulty while the screen keyboard is open.

The "Tap to type" button and keyboard tip disappear once the game sees a real key press on that device.

### Home-screen app

In Safari, tap **Share**, then **Add to Home Screen**. The game then opens full screen with its own icon. The player panel on iPad shows these steps until you hide them.

- **Offline:** published adventures you've loaded at least once stay playable offline. Updates arrive next time there's a connection. Editing always needs a connection.
- **Separate player data:** on iPad, the home-screen app keeps its own player data, apart from Safari's. Move players across with **Download data** in Safari, then **Import data** in the app.
- **App updates:** when you change `sw.js`, bump `VERSION` at the top so installed copies refresh their cached files. Changes to `index.html` and adventures arrive without it.

## Badges

Players earn 24 badges in seven groups:

| Group | Badges |
|---|---|
| Story | First Steps, Survivor, The Hard Way, Completionist (every ending in one adventure), Grand Tour (a best ending in every adventure) |
| Field notes | 10, 25 and 50 notes collected |
| Accuracy | Steady Hands (95%+ run), Flawless (no mistakes), Home Row Hero |
| Practice | Keyboard Explorer (every letter), 1,000 / 5,000 / 20,000 correct keys |
| Speed | 15, 25 and 40 words per minute in a finished run |
| Against the clock | Beat the Clock, Cool Under Pressure (10 timed scenes), Daredevil (best ending on Challenging or Expert) |
| Keep it up | Played on 3, 10 and 30 different days |

Badges are worked out from each player's saved data, so earlier play counts. New badges pop up while playing and are listed on the ending screen. The player panel shows recent badges and opens the full gallery, where locked badges show what's needed.

When `SHOW_TYPING_SPEED` is `false`, speed badges are hidden but still earned, so they appear if you switch speed back on. "Beat the Clock" badges only count when timers are on. Grand Tour and Completionist count published adventures only, so a new adventure gives players something new to earn.

To add or change badges, edit the `BADGES` list in `index.html`. Each badge has an id, a group, a name, a description and a rule.

## Player data

The game records each player's typing speed in three places:
- overall, across everything they've typed
- in each finished run's score
- in their in-progress save

Speed counts only correct keystrokes during active typing, so time spent reading a scene doesn't drag it down.


Player profiles, difficulty, saved progress, scores, key stats, typing speed and badges stay in each player's browser (localStorage), not on the server. Use **Download data** and **Import data** in the player panel to back them up or move them to another computer.
