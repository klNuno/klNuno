"""Merge the three cards into a single SVG.

Reason this exists: the README can only size an image with the HTML `width`
attribute, and Firefox ignores percentages there (they were dropped from the
spec, Chrome still honours them). GitHub also strips `style` from README HTML,
so no CSS is available either. Two images side by side therefore cannot be laid
out reliably. One image can: the gutters live inside the SVG, in user units, and
every browser scales the whole thing as a block.

Each card is embedded as a base64 data URI inside an <image> element rather than
inlined as a nested <svg>. The cards come from two different generators and both
ship their own <style> block with unscoped class names; nesting them in one
document would let those rules collide. A data URI is a separate document, so
the isolation is total.
"""

import base64
import pathlib
import re

CARDS = pathlib.Path(__file__).resolve().parent.parent / "cards"
GUTTER = 14.0
CANVAS = 1000.0


def load(name):
    raw = CARDS.joinpath(name).read_bytes()
    text = raw.decode("utf-8")
    box = re.search(r"viewBox=['\"]\s*0\s+0\s+([\d.]+)\s+([\d.]+)", text)
    if not box:
        raise SystemExit(f"{name}: no viewBox, refusing to guess its size")
    uri = "data:image/svg+xml;base64," + base64.b64encode(raw).decode("ascii")
    return float(box.group(1)) / float(box.group(2)), uri


def tag(x, y, w, h, uri):
    return (
        f'<image x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" '
        f'preserveAspectRatio="xMidYMid meet" href="{uri}"/>'
    )


wide_ratio, wide_uri = load("profile.svg")
left_ratio, left_uri = load("streak.svg")
right_ratio, right_uri = load("productive-time.svg")

wide_h = CANVAS / wide_ratio

# Both cards on the second row get the same height, so their baselines line up
# whatever their native sizes are.
row_h = (CANVAS - GUTTER) / (left_ratio + right_ratio)
left_w = row_h * left_ratio
right_w = row_h * right_ratio
row_y = wide_h + GUTTER
total_h = row_y + row_h

svg = (
    f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {CANVAS:.0f} {total_h:.2f}" '
    f'width="{CANVAS:.0f}" height="{total_h:.2f}" fill="none">'
    + tag(0, 0, CANVAS, wide_h, wide_uri)
    + tag(0, row_y, left_w, row_h, left_uri)
    + tag(left_w + GUTTER, row_y, right_w, row_h, right_uri)
    + "</svg>"
)

out = CARDS / "board.svg"
out.write_text(svg, encoding="utf-8")
print(f"board.svg {out.stat().st_size / 1024:.0f} KB, {CANVAS:.0f}x{total_h:.0f}")
