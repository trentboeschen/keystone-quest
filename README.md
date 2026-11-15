# Keystone Quest

A typing game for kids: branching history adventures where you type your choices.

## What's in this folder

| File | What it does |
|---|---|
| `index.html` | The game and the adventure editor. |
| `api.php` | Reads and writes the adventure files. |
| `config.php-sample` | Template for your settings. Copy it to `config.php`. |
| `config.php` | Your editor password and backup setting. You create it; git ignores it, so your password never gets committed. |
| `adventures/` | One `.json` file per adventure. The game loads every valid file in here; there is no manifest. |
| `adventures/.htaccess` | Stops people downloading the files directly, so drafts stay hidden (Apache only). |

## Setup

1. Upload the whole folder to your server, for example to `/typing/`, or clone the repository there.
2. Copy `config.php-sample` to `config.php`, next to `api.php`, and change `EDIT_PASSWORD` from `change-me` to your own password:

   ```
   cp config.php-sample config.php
   ```
3. Make sure PHP can write to the `adventures/` folder. On most hosts that means permissions `775` (or `777` on some shared hosts) on `adventures/`.
4. Open the folder's URL in a browser. Click **Editor** and enter your password to create and edit adventures.

Until `config.php` exists, the game shows a setup message instead of the adventures.

Needs PHP 7.4 or newer. No database.

### Updating from git

Run `git pull` on the server. Your `config.php` and the `adventures/_backups/` folder are ignored by git, so pulling never overwrites them.

Adventures you create or edit on the server change files in `adventures/`. To keep them in the repository, commit them from the server, or download them with **Export** and commit them from your own computer. If you edit the same adventure in both places, `git pull` reports a conflict instead of silently replacing either version.

### If your server uses nginx instead of Apache

`.htaccess` is ignored, so add this to your site config to keep drafts private:

```
location ^~ /typing/adventures/ { deny all; }
```

(Adjust `/typing/` to wherever you put the game.)

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

**Scenes:**
- `ending` is `good`, `mixed` or `bad`, or left out for a normal scene.
- `timer` (seconds) and `timeout` (scene to jump to) are optional.
- On a choice, `needs`, `lacks` and `gives` are comma-separated item names. Use them to show or hide choices based on what the player has picked up.

## Adding adventures

- **In the game:** sign in as editor, then use **New adventure**, **Duplicate** or **Import**. Saving writes straight to `adventures/`.
- **By hand:** drop a `.json` file into `adventures/`. It appears on the next page load. Turn on `published` when it's ready.

## Safety nets

- Every save and delete first copies the old version to `adventures/_backups/`. The last 20 per adventure are kept; you can change that with `BACKUPS_PER_ADVENTURE` in `config.php`. To restore one, copy it back into `adventures/` with the original file name.
- If someone saves an adventure after you opened it (another tab, another person, or a hand edit on the server), the editor warns you. You can then choose to overwrite their version or load it.

## Player data

Player profiles, saved progress, scores and key stats stay in each player's browser (localStorage), not on the server. Use **Download data** and **Import data** in the player panel to back them up or move them to another computer.
