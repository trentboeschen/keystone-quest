#!/usr/bin/env python3
"""Validate Keystone Quest adventure files.

Usage:
    python3 validate_adventure.py adventures/pompeii.json [more.json ...]

Checks everything the game and api.php rely on, plus the writing rules that
keep adventures fair to young typists. It also plays every path through the
adventure (tracking items from gives/needs/lacks) to prove that no player
can get stuck and that every ending can be reached.

Exit code 0 = no errors (warnings allowed), 1 = errors found.
"""
import json
import re
import sys
from collections import deque
from pathlib import Path

ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
SCENE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")
HEX_RE = re.compile(r"^#[0-9a-fA-F]{6}$")
TYPABLE = set("abcdefghijklmnopqrstuvwxyz ,.;'/")  # the keys drawn on the game's keyboard
ARTS = {"none", "volcano", "desert", "castle", "sea"}
ENDINGS = {"good", "mixed", "bad"}
TOP_KEYS = ["id", "title", "era", "blurb", "art", "accent", "published", "updated", "start", "scenes"]


def flags(value):
    return [t.strip().lower() for t in str(value or "").split(",") if t.strip()]


def words(text):
    return len(str(text or "").split())


def validate(path):
    errors, warnings = [], []
    err, warn = errors.append, warnings.append

    try:
        a = json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        return [f"not valid JSON: {e}"], []
    if not isinstance(a, dict):
        return ["top level must be an object"], []

    stem = Path(path).stem
    # --- listing info ---
    if not ID_RE.match(stem):
        err(f"file name '{stem}' must be lowercase letters, numbers and dashes")
    if a.get("id") not in (None, stem):
        err(f"id '{a.get('id')}' must match the file name '{stem}'")
    for k in ("title", "era", "blurb"):
        if not isinstance(a.get(k), str) or not a.get(k).strip():
            err(f"'{k}' is required")
    if words(a.get("blurb")) > 25:
        warn(f"blurb is {words(a.get('blurb'))} words; keep it to one line (under 25)")
    if a.get("art") not in ARTS:
        err(f"art must be one of {sorted(ARTS)}")
    if not isinstance(a.get("accent"), str) or not HEX_RE.match(a.get("accent", "")):
        err("accent must be a #rrggbb colour")
    if not isinstance(a.get("published"), bool):
        err("published must be true or false")
    for k in TOP_KEYS:
        if k not in a and k not in ("id", "updated"):
            err(f"missing top-level field '{k}'")
    if "sources" in a:
        src = a["sources"]
        if not isinstance(src, list) or not all(isinstance(s, dict) and s.get("url") for s in src):
            err("sources must be a list of {title, url} objects")

    scenes = a.get("scenes")
    if not isinstance(scenes, dict) or not scenes:
        err("scenes must be a non-empty object")
        return errors, warnings
    start = a.get("start")
    if start not in scenes:
        err(f"start scene '{start}' does not exist")

    # --- each scene ---
    for sid, s in scenes.items():
        where = f"scene '{sid}'"
        if not SCENE_RE.match(sid):
            err(f"{where}: name must be letters, numbers, dashes or underscores")
        if not isinstance(s, dict):
            err(f"{where}: must be an object")
            continue
        text = s.get("text")
        if not isinstance(text, str) or not text.strip():
            err(f"{where}: needs story text")
        elif words(text) > 70:
            warn(f"{where}: story is {words(text)} words; aim for 25-60")
        if s.get("fact") and words(s.get("fact")) > 45:
            warn(f"{where}: field note is {words(s['fact'])} words; aim for under 40")
        ending = s.get("ending")
        if ending not in (None, "", *ENDINGS):
            err(f"{where}: ending must be good, mixed or bad")
        choices = s.get("choices", [])
        if not isinstance(choices, list):
            err(f"{where}: choices must be a list")
            continue
        if ending:
            if choices:
                warn(f"{where}: endings ignore their choices; remove them")
            if s.get("timer"):
                warn(f"{where}: endings ignore timers")
            continue
        if not choices:
            err(f"{where}: not an ending, so it needs at least one choice")
        timer = s.get("timer")
        if timer not in (None, "", 0):
            if not isinstance(timer, (int, float)) or timer <= 0:
                err(f"{where}: timer must be a number of seconds")
            elif s.get("timeout") not in scenes:
                err(f"{where}: has a timer, so 'timeout' must name an existing scene")
            else:
                need = 4 + words(text) / 3 + max((len(c.get("text", "")) for c in choices), default=0) / 2
                if timer < need:
                    warn(f"{where}: {timer}s may be too short to read and type (suggest at least {round(need)}s)")
        texts = []
        for i, c in enumerate(choices, 1):
            cw = f"{where} choice {i}"
            if not isinstance(c, dict):
                err(f"{cw}: must be an object")
                continue
            t = c.get("text", "")
            if not isinstance(t, str) or not t.strip():
                err(f"{cw}: needs text")
                continue
            if t != t.lower():
                err(f"{cw}: '{t}' must be lowercase")
            if t != " ".join(t.split()):
                err(f"{cw}: '{t}' has extra spaces")
            bad = sorted(set(t.lower()) - TYPABLE)
            if bad:
                err(f"{cw}: '{t}' uses characters not on the game keyboard: {''.join(bad)}")
            if set(t) & set(",.;'/"):
                warn(f"{cw}: '{t}' has punctuation; plain words are easier for beginners")
            n = words(t)
            if n < 2 or n > 7:
                warn(f"{cw}: '{t}' is {n} words; aim for 3-6")
            if c.get("next") not in scenes:
                err(f"{cw}: next scene '{c.get('next')}' does not exist")
            texts.append(t)
        if len(texts) > 1:
            lens = [len(t) for t in texts]
            if max(lens) - min(lens) > 10:
                warn(f"{where}: choice lengths range {min(lens)}-{max(lens)} letters; keep them within about 8 so the shortest isn't the easy pick")
            firsts = [t.split()[0] for t in texts]
            if len(set(firsts)) < len(firsts):
                warn(f"{where}: two choices start with the same word; the fade-out hint won't help until later")

    # --- play every path, tracking items ---
    if start in scenes:
        def visible(s, have):
            return [c for c in s.get("choices", []) if isinstance(c, dict) and c.get("text")
                    and all(f in have for f in flags(c.get("needs")))
                    and not any(f in have for f in flags(c.get("lacks")))]

        seen, endings_hit, scenes_hit = set(), set(), set()
        q = deque([(start, frozenset())])
        while q:
            sid, have = q.popleft()
            if (sid, have) in seen or sid not in scenes:
                continue
            seen.add((sid, have))
            scenes_hit.add(sid)
            s = scenes[sid]
            if not isinstance(s, dict):
                continue
            if s.get("ending"):
                endings_hit.add(sid)
                continue
            vis = visible(s, have)
            if not vis:
                err(f"scene '{sid}': a player carrying {sorted(have) or 'nothing'} sees no choices and is stuck")
            low = [c["text"].lower() for c in vis]
            for x in low:
                for y in low:
                    if x != y and y.startswith(x):
                        err(f"scene '{sid}': '{x}' is the start of '{y}', so typing the longer one always picks the shorter")
                if low.count(x) > 1:
                    err(f"scene '{sid}': two visible choices are both '{x}'")
            for c in vis:
                q.append((c.get("next"), have | frozenset(flags(c.get("gives")))))
            if s.get("timer") and s.get("timeout") in scenes:
                q.append((s["timeout"], have))
        all_endings = {k for k, s in scenes.items() if isinstance(s, dict) and s.get("ending")}
        for k in sorted(set(scenes) - scenes_hit):
            err(f"scene '{k}' can never be reached")
        for k in sorted(all_endings - endings_hit):
            err(f"ending '{k}' can never be reached")
        kinds = {scenes[k].get("ending") for k in all_endings}
        if len(all_endings) < 2:
            warn("only one ending; aim for 3-5 so choices matter")
        if "good" not in kinds:
            err("needs at least one 'good' ending")
        if not any(s.get("timer") for s in scenes.values() if isinstance(s, dict)):
            warn("no timed scenes; one or two tense moments make it more exciting")
        if not any(s.get("fact") for s in scenes.values() if isinstance(s, dict)):
            warn("no field notes; most scenes should teach one true fact")
        given = {f for s in scenes.values() if isinstance(s, dict) for c in s.get("choices", []) if isinstance(c, dict) for f in flags(c.get("gives"))}
        needed = {f for s in scenes.values() if isinstance(s, dict) for c in s.get("choices", []) if isinstance(c, dict) for f in flags(c.get("needs"))}
        for f in sorted(needed - given):
            err(f"item '{f}' is needed by a choice but no choice gives it")
        n = len(scenes)
        if n < 10:
            warn(f"only {n} scenes; aim for 14-22")
    return errors, warnings


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    failed = False
    for p in argv[1:]:
        errors, warnings = validate(p)
        status = "FAIL" if errors else "OK"
        print(f"{status}  {p}  ({len(errors)} errors, {len(warnings)} warnings)")
        for e in errors:
            print(f"  error:   {e}")
        for w in warnings:
            print(f"  warning: {w}")
        failed |= bool(errors)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
