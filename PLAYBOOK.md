# A logo for every Herdr space: the playbook

This file is written for a coding agent (Claude Code, Codex, Grok) and is
readable by a person. Do the steps in order. Each step is one action, a
"Verify:" command and the result to expect. Stop at the first result that
does not match and report what you saw.

Agents: steps 1 to 4 change nothing outside this repo and the config folder.
Steps 5 to 8 change the person's Herdr window: ask before each of them.

## Goal

The Herdr desktop app shows a logo, or a letter tile with a chosen letter and
color, in front of each space the person lists, in the spaces sidebar and in
the Go to picker. Every other space looks as it did. One command undoes it.

## Before you start

The Herdr home is the folder the desktop app keeps its files in:
`$HERDR_APP_HOME` when that is set, else `~/.config/herdr-app`. The commands
below spell it out in full, because an agent's shell may not keep variables
from one command to the next.

| Need | Check | Expected | If it fails |
|---|---|---|---|
| Python 3.11 or newer | `python3 -c 'import sys; print(sys.version_info >= (3, 11))'` | `True` | install a newer Python from python.org or your package manager |
| git | `git --version` | a version line | install git |
| The Herdr desktop app's command line | `command -v herdr-app` | a path | install the desktop app from herdr.dev; the terminal app `herdr` has no mods, so it cannot show logos |
| A Herdr home with Herdr's own mods in it | `test -f "${HERDR_APP_HOME:-$HOME/.config/herdr-app}/mods/spaces/main.js" && echo ok` | `ok` | start the desktop app once (it writes its mods on every start), or set `HERDR_APP_HOME` to the right folder |
| node (optional) | `node --version` | a version line | nothing to do: two tests are skipped without it |

## Steps

### 1. Run the demo on the synthetic data

This installs into a temporary copy of a made-up Herdr home
(`examples/herdr-home`), undoes it, and checks the copy is back as it was.
Nothing on your machine changes.

```bash
bash examples/run.sh
```

Verify: `bash examples/run.sh | diff - examples/expected-output.txt && echo same`
Expected: `same`

### 2. Make your config folder

The config is a `spaces.json` file with a `logos/` folder next to it. Start
from the example, so the next step has something to check.

```bash
mkdir -p ~/.config/herdr-space-logos/logos
cp -n examples/spaces.json ~/.config/herdr-space-logos/spaces.json
cp -n examples/logos/*.svg ~/.config/herdr-space-logos/logos/
```

Verify: `python3 src/space_logos.py check | tail -n 1`
Expected: `check: ok (nothing was written)`

This check reads your real Herdr's `spaces` and `picker` mods and patches
them in memory only. If it stops with "Herdr changed its ... mod", your Herdr
version draws its tiles differently: go to "When Herdr changes its mods"
below before you go on.

### 3. Find the exact names of your spaces

Logos go by a space's exact name, as the sidebar shows it, spaces and dots
included.

```bash
herdr-app ls
```

Verify: `herdr-app ls | head -n 20`
Expected: your spaces, with their tabs and terminals. Note each name you want a logo for.

### 4. Write your spaces and logos into the config

Open `~/.config/herdr-space-logos/spaces.json`. Replace the example spaces
with yours. For each one, give either a logo or a letter tile:

- A logo: put the file in `~/.config/herdr-space-logos/logos/` (SVG, or PNG
  of at least 64 px; a square symbol reads best at 18 px) and write
  `"my space": { "logo": "file.svg" }`. Add `"bg": "#rrggbb"` for a tile color
  behind it and `"pad": 2` for a margin in pixels.
- A letter tile: `"my space": { "letter": "D", "color": "#3a7bd5" }`. The
  letter can be one or two characters; `"text"` sets its color (default white).
  Leave out `letter` to keep the space's own letter, and `color` to keep
  Herdr's color.

The example keeps `"separator": " · "`: with it, a space without its own
letter shows the first letter after the separator (`acme · WEB` shows W),
for every space, listed or not. Delete that line to keep Herdr's rule, the
first letter of the name.

Delete the example logos you do not use.

Verify: `python3 src/space_logos.py check`
Expected: one line per space of yours with the tile it gets, then `check: ok (nothing was written)`.

### 5. Clone Herdr's main layout

Herdr's own layouts and mods are read-only: Herdr rewrites them on every
start. So the logos go into copies. This command copies the `main` layout as
`logos` and switches the window to it; nothing looks different yet. If you
already use a layout of your own (a clone), skip this step and use its name
in step 6.

```bash
herdr-app do layout.clone '{"name":"main","as":"logos"}'
```

Verify: `test -f "${HERDR_APP_HOME:-$HOME/.config/herdr-app}/layouts/logos.json" && echo ok`
Expected: `ok`

### 6. Install the logo mods and point the layout at them

This writes two new mods into the Herdr home, `mods/logo-spaces/` (with your
logos) and `mods/logo-picker/`, made from Herdr's own `spaces` and `picker`
mods with three exact edits each. Then it points the `logos` layout at them,
after a one-time backup of the layout file. The sidebar changes within a
second: Herdr reloads mods and layouts when their files change.

```bash
python3 src/space_logos.py install --layout logos
```

Verify: `herdr-app check "${HERDR_APP_HOME:-$HOME/.config/herdr-app}/mods/logo-spaces" && herdr-app check "${HERDR_APP_HOME:-$HOME/.config/herdr-app}/mods/logo-picker" && echo ok`
Expected: `ok` (`herdr-app check` loads a mod, draws it once and exits non-zero with the error when it fails)

### 7. Look at the sidebar

Verify: `herdr-app status`
Expected: the layout `logos`, and no error from files or mods. In the window, each space you listed shows its logo or letter tile.

`herdr-app shot` saves a picture of the window if you want to show someone.

### 8. Optional: the Go to picker too

The picker opens from a key in `keys.json` (`ctrl-shift-k` by default). This
points every key that opens Herdr's picker at the logo picker, after a
one-time backup of `keys.json`. The trade-off: once you edit `keys.json`,
Herdr treats the file as yours and stops adding its new default keys to it on
upgrades. `undo` puts the original file back.

```bash
python3 src/space_logos.py install --layout logos --keys
```

Verify: `grep -c 'mod.open:logo-picker' "${HERDR_APP_HOME:-$HOME/.config/herdr-app}/keys.json"`
Expected: a number, 1 or more. Press `ctrl-shift-k`: the space headers show the same tiles as the sidebar.

## Adapt it

Change a setting, then run step 6 again (`install` is safe to run again: it
rewrites only the folders it made and keeps the first backups).

| Setting | Where | Example |
|---|---|---|
| A space's logo | `~/.config/herdr-space-logos/spaces.json`, under `spaces` | `"acme · WEB": { "logo": "acme.svg" }` |
| A tile color behind a logo, and its margin | the same entry: `bg`, `pad` (0 to 6 px) | `"demo-api": { "logo": "peak.svg", "bg": "#1d2b4f", "pad": 3 }` |
| A letter tile | the same entry: `letter`, `color`, `text` | `"docs": { "letter": "D", "color": "#3a7bd5" }` |
| The letter after a separator, for every space | top-level `separator` | `"separator": " · "` makes `acme · WEB` show W, not A |
| The logos folder | top-level `logos`, relative to spaces.json | `"logos": "logos"` |
| The names of the two new mods | top-level `spaces_mod`, `picker_mod` | `"spaces_mod": "logo-spaces"` |
| Where the config is | env `SPACE_LOGOS_CONFIG`, or `--config` | `--config ./my-spaces.json` |
| Where the Herdr home is | env `HERDR_APP_HOME`, or `--home` | `--home ~/.config/herdr-app` |
| Which layout shows the logos | `install --layout NAME` | `--layout logos` |
| A picture of your config | `preview --svg FILE` | `python3 src/space_logos.py preview --svg tiles.svg` |

## When Herdr changes its mods

The two mods are copies, so they do not follow Herdr updates. After you
update Herdr, run step 6 again to rebuild them from the new shipped mods.

The patch looks for three pieces of code (its anchors) in each of Herdr's
`spaces` and `picker` mods. If `check` or `install` stops with "Herdr changed
its spaces mod" (or picker), one of them moved, and the message names which.
Nothing was written, and your old copies keep working.

| Anchor | What the tool does there | When it is gone, the message says |
|---|---|---|
| The `gpui-kit` import, `import { ... } from "gpui-kit";`, on one line or several | adds `image` to it | "the anchor for the gpui-kit import" |
| The last `import` statement | puts the logo code after it | it cannot go missing while the gpui-kit import is there |
| The space's letter tile | puts `spaceLogoTile(...)` in its place | "the anchor for the space's letter tile" |

The letter tile anchor runs from the `child(` that holds the tile's
`h_flex()` to the parenthesis that closes it. In Herdr 0.1.15 the `spaces`
mod has it as one line:

```js
el.child(h_flex().size(18).flex_none().rounded(5).bg(fill).items_center().justify_center().text_size(10.5).font_bold().text_color("#ffffff").child([...w.name][0]?.toUpperCase() ?? "?"))
```

and the `picker` mod as:

```js
.child(h_flex().size(18).rounded(5).bg(spaceColor(t, r.w)).items_center().justify_center().text_size(10.5).font_bold().text_color("#ffffff").child([...r.w.name][0]?.toUpperCase() ?? "?"))
```

To update the letter tile anchor:

1. Open Herdr's shipped mod, for example
   `"${HERDR_APP_HOME:-$HOME/.config/herdr-app}/mods/spaces/main.js"`, and
   search for `toUpperCase() ?? "?"`.
2. Copy the whole expression, from `el.child(h_flex()` (spaces) or
   `.child(h_flex()` (picker) to the parenthesis that closes it, into
   `TILE_EDITS` in `src/space_logos.py` (the first string of the pair). Keep
   the replacement (the second string) passing the same two values: the
   space and its color.
3. Put the same new line in the stand-in mod under `examples/herdr-home/mods/`,
   so the tests match the new Herdr.
4. Run `./check.sh`, then step 2's check.

When the message names the gpui-kit import, the mod no longer has exactly
one `import { ... } from "gpui-kit";` statement. Look at the imports at the
top of the shipped mod. If Herdr now splits them in two statements, or
imports from another module name, change `GPUI_IMPORT` in
`src/space_logos.py` to match the statement that holds `View`, write the new
shape into the stand-in mods, and run `./check.sh`.

## Done when

- `./check.sh` prints `check: ok`.
- `python3 src/space_logos.py check` lists your spaces and ends with `check: ok (nothing was written)`.
- `herdr-app check` passes for `mods/logo-spaces` and `mods/logo-picker` in the Herdr home.
- In the window, the spaces you listed show their logo or letter tile, and the others look as before.

## Undo

1. Switch the window back to Herdr's own layout, so it never shows a layout
   that names a removed mod:
   `herdr-app do layout.switch '{"name":"main"}'`
2. Remove what `install` did: `python3 src/space_logos.py undo`. It restores
   every file it changed from its backup (the layout, `keys.json`), then
   deletes the mod folders it made (each one carries a `.made-by-space-logos`
   file; it deletes no other folder).
3. If you made the `logos` layout only for this, delete it:
   `rm "${HERDR_APP_HOME:-$HOME/.config/herdr-app}/layouts/logos.json"`.
4. Delete the config folder: `rm -r ~/.config/herdr-space-logos`.

Verify: `ls "${HERDR_APP_HOME:-$HOME/.config/herdr-app}/mods" | grep -c '^logo-'`
Expected: `0`

## Safety

- Reads: `spaces.json` and its logos folder; Herdr's shipped `mods/spaces`
  and `mods/picker` (never changed); the layout you name with `--layout`;
  `keys.json` only with `--keys`.
- Writes, only inside the Herdr home: the two new mod folders, the layout you
  name and `keys.json` (each with one backup next to it, kept from the first
  change). `--layout` takes a name in `layouts/`, never a path: a name with a
  slash stops the tool. `preview` writes the SVG file you name. The demo and the tests
  write only to temporary folders.
- Never: changes Herdr's own mods or layouts (`main`, `terminals`, `win98`),
  overwrites a folder it did not make, runs a program (not `herdr-app`, not
  `hc`), uses the network, or reads secrets. The mods it writes run no
  program and fetch nothing: they show image files from the Herdr home.
