# Changelog

Every change a reader should know about, newest first.

## 0.1.1 - 2026-11-19

- `undo` takes out only its own edits: a layout or `keys.json` that changed
  after install keeps those changes, and its backup stays as
  `<file>.before-install`.
- `check` runs every check `install` runs (a mod folder this tool did not
  make, `--layout`, `--keys`), and `check --ls` names each space in
  `spaces.json` that no open space is called.
- A `gpui-kit` import over several lines, with a trailing comma, is patched
  into valid JavaScript.
- `--layout` takes a layout name, never a path.
- PLAYBOOK.md: the picker key per platform, the search button that still
  opens Herdr's picker, how to get the `herdr-app` command, what the
  separator does to spaces you did not list, all three anchors, and a
  caution on sharing a window picture.
- The scrub counts a commit e-mail that is not a noreply address as a
  finding.

## 0.1.0 - 2026-11-19

- First version: `src/space_logos.py` with `check`, `install`, `undo`,
  `preview` and `--demo`; a synthetic example; offline tests.
- The patch anchors come from the `spaces` and `picker` mods of the Herdr
  desktop app 0.1.15.
