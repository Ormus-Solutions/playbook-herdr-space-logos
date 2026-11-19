// A synthetic stand-in for Herdr's shipped `picker` mod (see ../../README.md).
// It lists the spaces as the Go to picker's group headers, each with its tile.
import { View, div, svg } from "gpui-kit";
import { v_flex, h_flex } from "gpui-base";
import { spaces, theme } from "herdr";

function spaceColor(t, _p) {
  return t.accent;
}

export default class Picker extends View {
  render() {
    const t = theme();
    const rows = spaces().map((w) => ({ w }));
    return v_flex().id("picker").gap(4).children(rows.map((r) =>
      h_flex().id(`row-${r.w.id}`).gap(8).items_center()
        .child(h_flex().size(18).rounded(5).bg(spaceColor(t, r.w)).items_center().justify_center().text_size(10.5).font_bold().text_color("#ffffff").child([...r.w.name][0]?.toUpperCase() ?? "?"))
        .child(div().child(r.w.name))));
  }
}
