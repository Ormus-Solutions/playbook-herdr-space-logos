// A synthetic stand-in for Herdr's shipped `spaces` mod (see ../../README.md).
// It lists the spaces, each with Herdr's letter tile; a worktree space ("tree")
// shows no tile.
import { View, div, svg } from "gpui-kit";
import { v_flex, h_flex } from "gpui-base";
import { spaces, theme } from "herdr";

export default class Spaces extends View {
  render() {
    const t = theme();
    return v_flex().size_full().gap(4).children(spaces().map((w) => {
      const fill = t.accent;
      const tree = Boolean(w.branch && w.worktree);
      return h_flex().id(`space-${w.id}`).gap(8).items_center()
        .when(!tree, el => el.child(h_flex().size(18).flex_none().rounded(5).bg(fill).items_center().justify_center().text_size(10.5).font_bold().text_color("#ffffff").child([...w.name][0]?.toUpperCase() ?? "?")))
        .child(div().child(w.name));
    }));
  }
}
