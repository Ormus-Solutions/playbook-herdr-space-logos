"""Offline tests: they pin the behaviour on synthetic data, with no setup.

Run them with: python3 -m unittest discover -s tests
They never touch a real Herdr home: each test works in its own temporary copy
of examples/herdr-home. The two node tests run only when node is installed.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
sys.path.insert(0, str(ROOT / "src"))

import space_logos as sl  # the reference implementation in src/space_logos.py


class TempHome(unittest.TestCase):
    """A fresh copy of the synthetic Herdr home and of the example config."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.home = self.tmp / "herdr-home"
        shutil.copytree(EXAMPLES / "herdr-home", self.home)
        shutil.copytree(EXAMPLES / "logos", self.tmp / "logos")
        self.config_file = self.tmp / "spaces.json"
        shutil.copyfile(EXAMPLES / "spaces.json", self.config_file)
        self.config = sl.load_config(self.config_file)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def write_config(self, data: dict) -> Path:
        self.config_file.write_text(json.dumps(data), encoding="utf-8")
        return self.config_file

    def stops(self, data: dict, says: str) -> None:
        with self.assertRaises(SystemExit) as caught:
            sl.load_config(self.write_config(data))
        self.assertIn(says, str(caught.exception))


class ConfigTest(TempHome):
    def test_missing_config_says_what_to_do(self) -> None:
        with self.assertRaises(SystemExit) as caught:
            sl.load_config(self.tmp / "nope.json")
        self.assertIn("examples/spaces.json", str(caught.exception))

    def test_the_example_config_loads(self) -> None:
        self.assertEqual(len(self.config.spaces), 7)
        self.assertEqual((self.config.spaces_mod, self.config.picker_mod), ("logo-spaces", "logo-picker"))

    def test_bad_entries_stop_with_the_reason(self) -> None:
        cases = [
            ({"spaces": {}}, "at least one space"),
            ({"spaces": {"a": {"logo": "acme.svg"}}, "colour": 1}, "unknown key"),
            ({"spaces": {"a": {"icon": "acme.svg"}}}, "unknown key"),
            ({"spaces": {"a": {"logo": "missing.svg"}}}, "not in logos/"),
            ({"spaces": {"a": {"logo": "../acme.svg"}}}, "file name like"),
            ({"spaces": {"a": {"logo": "acme.svg", "letter": "A"}}}, "not both"),
            ({"spaces": {"a": {"bg": "#000000"}}}, "go with a logo"),
            ({"spaces": {"a": {"logo": "acme.svg", "pad": 9}}}, "0 to 6"),
            ({"spaces": {"a": {"color": "blue"}}}, "a color like"),
            ({"spaces": {"a": {"letter": "ABC"}}}, "one or two characters"),
            ({"spaces": {" ": {"letter": "A"}}}, "empty"),
            ({"spaces": {"a": {}}, "spaces_mod": "spaces"}, "not Herdr's own"),
            ({"spaces": {"a": {}}, "spaces_mod": "x", "picker_mod": "x"}, "two different names"),
        ]
        for data, says in cases:
            with self.subTest(says=says):
                self.stops(data, says)

    def test_comment_keys_are_allowed(self) -> None:
        cfg = sl.load_config(self.write_config({"$comment": "hi", "spaces": {"a": {}}}))
        self.assertEqual(list(cfg.spaces), ["a"])


class LetterTest(unittest.TestCase):
    def test_without_a_separator_it_is_herdrs_rule(self) -> None:
        self.assertEqual(sl.letter_for("acme · WEB", ""), "A")
        self.assertEqual(sl.letter_for("docs", ""), "D")

    def test_with_a_separator_it_is_the_letter_after_it(self) -> None:
        self.assertEqual(sl.letter_for("acme · WEB", " · "), "W")
        self.assertEqual(sl.letter_for("docs", " · "), "D")
        self.assertEqual(sl.letter_for("acme · ", " · "), "A")

    def test_an_empty_name_gets_a_question_mark(self) -> None:
        self.assertEqual(sl.letter_for("", ""), "?")


class PatchTest(TempHome):
    def base(self, which: str) -> str:
        return (self.home / "mods" / which / "main.js").read_text(encoding="utf-8")

    def test_both_mods_get_three_edits(self) -> None:
        block = sl.tile_js(self.config)
        for which in ("spaces", "picker"):
            with self.subTest(which=which):
                code, edits = sl.patch(self.base(which), which, block)
                self.assertEqual(edits, 3)
                self.assertIn('import { View, div, svg, image } from "gpui-kit";', code)
                self.assertEqual(code.count(sl.BLOCK_START), 1)
                self.assertNotIn("toUpperCase() ?? \"?\"))", code.split(sl.BLOCK_END)[1])
                self.assertIn(sl.TILE_EDITS[which][1], code)

    def test_logo_paths_point_into_the_spaces_mod(self) -> None:
        table = sl.tile_table(self.config)
        self.assertEqual(table["acme · WEB"]["logo"], "mods/logo-spaces/logos/acme.svg")
        self.assertEqual(table["docs"], {"letter": "D", "color": "#3a7bd5"})

    def test_a_moved_anchor_stops_the_build(self) -> None:
        src = self.base("spaces").replace(".font_bold()", ".font_semibold()")
        with self.assertRaises(SystemExit) as caught:
            sl.patch(src, "spaces", sl.tile_js(self.config))
        self.assertIn("Herdr changed its spaces mod", str(caught.exception))

    def test_an_already_patched_file_is_refused(self) -> None:
        code, _ = sl.patch(self.base("picker"), "picker", sl.tile_js(self.config))
        with self.assertRaises(SystemExit) as caught:
            sl.patch(code, "picker", sl.tile_js(self.config))
        self.assertIn("already patched", str(caught.exception))

    def test_an_image_import_already_there_is_kept(self) -> None:
        src = self.base("spaces").replace("{ View, div, svg }", "{ View, div, svg, image }")
        code, edits = sl.patch(src, "spaces", sl.tile_js(self.config))
        self.assertEqual(edits, 2)
        self.assertEqual(code.count("image }"), 1)


class InstallTest(TempHome):
    def test_install_writes_both_mods_and_the_logos(self) -> None:
        sl.install(self.config, self.home, layout=None, keys=False)
        spaces = self.home / "mods" / "logo-spaces"
        self.assertTrue((spaces / sl.MARKER).is_file())
        self.assertEqual(sorted(p.name for p in (spaces / "logos").iterdir()),
                         ["acme.svg", "orbit.svg", "peak.svg"])
        meta = json.loads((self.home / "mods" / "logo-picker" / "mod.json").read_text())
        self.assertEqual(meta["title"], "Picker (logos)")
        self.assertEqual(meta["overlay"]["kind"], "popup")

    def test_herdrs_shipped_mods_are_never_changed(self) -> None:
        before = sl.snapshot(self.home / "mods")
        sl.install(self.config, self.home, layout="logos", keys=True)
        after = sl.snapshot(self.home / "mods")
        for path, digest in before.items():
            self.assertEqual(after[path], digest, path)

    def test_a_folder_it_did_not_make_is_never_overwritten(self) -> None:
        (self.home / "mods" / "logo-spaces").mkdir()
        with self.assertRaises(SystemExit) as caught:
            sl.install(self.config, self.home, layout=None, keys=False)
        self.assertIn("did not make it", str(caught.exception))
        self.assertFalse((self.home / "mods" / "logo-picker").exists())

    def test_a_second_install_drops_old_logos_and_keeps_herdrs_files(self) -> None:
        sl.install(self.config, self.home, layout=None, keys=False)
        folder = self.home / "mods" / "logo-spaces"
        (folder / "gpui-kit.d.ts").write_text("// written by Herdr\n")
        data = json.loads(self.config_file.read_text())
        data["spaces"] = {"acme · WEB": {"logo": "acme.svg"}}
        sl.install(sl.load_config(self.write_config(data)), self.home, layout=None, keys=False)
        self.assertEqual([p.name for p in (folder / "logos").iterdir()], ["acme.svg"])
        self.assertTrue((folder / "gpui-kit.d.ts").is_file())

    def test_the_layout_points_at_the_new_mods(self) -> None:
        line = sl.use_in_layout(self.home, "logos", self.config)
        self.assertIn("1 block now uses", line)
        layout = json.loads((self.home / "layouts" / "logos.json").read_text())
        sidebar = layout["children"][0]["children"]
        self.assertEqual(sidebar[0]["content"]["mod"], "logo-spaces")
        self.assertEqual(sidebar[1]["content"]["mod"], "agents")
        self.assertIn("already uses", sl.use_in_layout(self.home, "logos", self.config))

    def test_the_first_backup_is_kept(self) -> None:
        original = (self.home / "layouts" / "logos.json").read_bytes()
        sl.use_in_layout(self.home, "logos", self.config)
        sl.use_in_layout(self.home, "logos", self.config)
        backup = self.home / "layouts" / ("logos.json" + sl.BACKUP)
        self.assertEqual(backup.read_bytes(), original)

    def test_herdrs_own_layouts_are_refused(self) -> None:
        for name in ("main", "terminals", "win98"):
            with self.subTest(name=name), self.assertRaises(SystemExit) as caught:
                sl.use_in_layout(self.home, name, self.config)
            self.assertIn("clone it first", str(caught.exception))

    def test_a_refused_layout_or_broken_keys_file_writes_nothing(self) -> None:
        before = sl.snapshot(self.home)
        with self.assertRaises(SystemExit):
            sl.install(self.config, self.home, layout="main", keys=True)
        self.assertEqual(sl.snapshot(self.home), before)
        (self.home / "keys.json").write_text("{ not json")
        before = sl.snapshot(self.home)
        with self.assertRaises(SystemExit) as caught:
            sl.install(self.config, self.home, layout="logos", keys=True)
        self.assertIn("keys.json is not valid JSON", str(caught.exception))
        self.assertEqual(sl.snapshot(self.home), before)

    def test_a_layout_without_the_spaces_mod_stops(self) -> None:
        (self.home / "layouts" / "bare.json").write_text('{"id": "root", "type": "row", "children": []}')
        with self.assertRaises(SystemExit) as caught:
            sl.use_in_layout(self.home, "bare", self.config)
        self.assertIn("no block with the spaces or picker mod", str(caught.exception))

    def test_keys_in_both_forms_point_at_the_new_picker(self) -> None:
        self.assertIn("2 keys now open logo-picker", sl.use_in_keys(self.home, self.config))
        keys = json.loads((self.home / "keys.json").read_text())["global"]
        self.assertEqual(keys["ctrl-shift-k"], "mod.open:logo-picker")
        self.assertEqual(keys["ctrl-space a"]["args"]["name"], "logo-picker")
        self.assertEqual(keys["ctrl-shift-t"], "tab.new")
        self.assertIn("already open logo-picker", sl.use_in_keys(self.home, self.config))

    def test_keys_without_the_picker_are_left_alone(self) -> None:
        (self.home / "keys.json").write_text('{"global": {"ctrl-shift-t": "tab.new"}}')
        self.assertIn("left as it is", sl.use_in_keys(self.home, self.config))
        self.assertFalse((self.home / ("keys.json" + sl.BACKUP)).exists())
        (self.home / "keys.json").unlink()
        self.assertIn("no keys.json", sl.use_in_keys(self.home, self.config))

    def test_a_home_without_herdrs_mods_says_so(self) -> None:
        shutil.rmtree(self.home / "mods" / "picker")
        with self.assertRaises(SystemExit) as caught:
            sl.plan(self.config, self.home)
        self.assertIn("is this the Herdr app home", str(caught.exception))


class UndoTest(TempHome):
    def test_undo_puts_every_file_back(self) -> None:
        before = sl.snapshot(self.home)
        sl.install(self.config, self.home, layout="logos", keys=True)
        self.assertNotEqual(sl.snapshot(self.home), before)
        sl.undo(self.home)
        self.assertEqual(sl.snapshot(self.home), before)

    def test_undo_leaves_other_mods_alone(self) -> None:
        mine = self.home / "mods" / "my-own"
        mine.mkdir()
        (mine / "main.js").write_text("// someone's mod\n")
        sl.install(self.config, self.home, layout=None, keys=False)
        lines = sl.undo(self.home)
        self.assertTrue(mine.is_dir())
        self.assertEqual(lines, ["  mods/logo-picker removed", "  mods/logo-spaces removed"])

    def test_nothing_to_undo(self) -> None:
        self.assertIn("nothing to undo", sl.undo(self.home)[0])


class ExampleTest(unittest.TestCase):
    def test_demo_prints_the_expected_output(self) -> None:
        done = subprocess.run(["bash", str(EXAMPLES / "run.sh")], capture_output=True, text=True, check=True)
        self.assertEqual(done.stdout, (EXAMPLES / "expected-output.txt").read_text(encoding="utf-8"))

    def test_the_preview_svg_is_made_from_the_example(self) -> None:
        config = sl.load_config(EXAMPLES / "spaces.json")
        self.assertEqual(sl.preview_svg(config), (EXAMPLES / "preview.svg").read_text(encoding="utf-8"),
                         "run: python3 src/space_logos.py preview --config examples/spaces.json "
                         "--svg examples/preview.svg")


@unittest.skipUnless(shutil.which("node"), "node is not installed")
class NodeTest(TempHome):
    def test_the_patched_mods_are_valid_javascript(self) -> None:
        sl.install(self.config, self.home, layout=None, keys=False)
        for name in ("logo-spaces", "logo-picker"):
            copy = self.tmp / f"{name}.mjs"
            shutil.copyfile(self.home / "mods" / name / "main.js", copy)
            done = subprocess.run(["node", "--check", str(copy)], capture_output=True, text=True)
            self.assertEqual(done.returncode, 0, done.stderr)

    def test_the_javascript_letter_rule_matches_the_python_one(self) -> None:
        names = ["acme · WEB", "acme ·   web", "docs", "acme · ", "élan · beta", "x·y", "", "lab · DASH · 2"]
        block = sl.tile_js(self.config)
        pure = block.split(sl.PURE_END)[0]
        script = self.tmp / "letters.mjs"
        script.write_text(pure + f"\nconsole.log(JSON.stringify({json.dumps(names)}.map(spaceLogoLetter)));\n")
        done = subprocess.run(["node", str(script)], capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(done.stdout), [sl.letter_for(n, " · ") for n in names])


if __name__ == "__main__":
    unittest.main()
