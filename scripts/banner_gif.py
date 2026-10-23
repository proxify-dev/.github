"""Render the public banner as an animated GIF of agentic-kit's use cases.

The scenes are read from the "You ask Claude | Claude runs | What came back" table
in agentic-kit's README, so a change there reaches the banner on the next run.

    uv run --with pillow python3 scripts/banner_gif.py
"""
import base64
import json
import pathlib
import re
import subprocess

from PIL import Image, ImageDraw, ImageFont

HERE = pathlib.Path(__file__).parent
FONTS = HERE / "fonts"
PROFILE = HERE.parent / "profile"

S = 2  # render at 2x for sharp text on retina screens
W, H = 1280 * S, 320 * S

THEMES = {
    "dark": dict(bg="#15172F", dot="#272594", label="#949BAD", title="#FFFFFF", tagline="#D5D5FE"),
    "light": dict(bg="#F5F5FF", dot="#D5D5FE", label="#667085", title="#15172F", tagline="#475467"),
}
# the terminal panel stays dark in both themes
PANEL, EDGE, WHITE, MUTED, ACCENT, GREEN = "#1D2939", "#344054", "#FFFFFF", "#949BAD", "#999AFD", "#12B76A"


def font(name, size):
    return ImageFont.truetype(str(FONTS / f"{name}.ttf"), size * S)


NAME, SANS_400 = font("inter_latest_latin-600-normal", 52), font("inter_latest_latin-400-normal", 26)
BODY = font("inter_latest_latin-400-normal", 20)
MONO, MONO_B = font("jetbrains-mono_latest_latin-400-normal", 16), font("jetbrains-mono_latest_latin-600-normal", 16)


def plain(md):
    md = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", md)
    return re.sub(r"[*`]", "", md).replace("&nbsp;", " ").strip()


def kit_readme():
    return base64.b64decode(json.loads(subprocess.run(
        ["gh", "api", "repos/proxify-dev/agentic-kit/readme"], check=True, capture_output=True, text=True).stdout)["content"]).decode()


def summary(readme):
    """The paragraph right after the bold tagline at the top of the kit README."""
    after = readme.split("**", 2)[2]
    return plain(" ".join(after.strip().split("\n\n")[0].split()))


def scenes(readme):
    rows, inside = [], False
    for line in readme.splitlines():
        if line.startswith("| You ask Claude"):
            inside = True
        elif inside and line.startswith("|---"):
            continue
        elif inside and line.startswith("|"):
            cells = [plain(c) for c in line.strip().strip("|").split(" | ")]
            ask, runs, came = cells[:3]
            rows.append([ask, runs, came.split(";")[0]])  # first clause reads cleanly in two lines
        elif inside:
            break
    return rows


# panel geometry (1x units, scaled by S)
PX, PY, PW, PH = 640, 56, 600, 208
COL = 100  # where text starts after the speaker label
LINE = 26


def wrap(text, fnt, width, max_lines):
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = f"{cur} {w}".strip()
        if fnt.getlength(trial) <= width:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        while fnt.getlength(lines[-1] + " ...") > width:
            lines[-1] = lines[-1].rsplit(" ", 1)[0]
        lines[-1] += " ..."
    return lines


def base(t, name, blurb):
    img = Image.new("RGB", (W, H), t["bg"])
    d = ImageDraw.Draw(img)
    for x in range(560 * S, W - 16 * S, 24 * S):
        for y in range(8 * S, H - 8 * S, 24 * S):
            d.ellipse([x, y, x + 2.4 * S, y + 2.4 * S], fill=t["dot"])
    # the banner is the section: repo name, then what it does in the README's own words
    lines = wrap(blurb, BODY, 470 * S, 4)
    top = (H / S - (64 + 30 * len(lines))) / 2
    d.text((56 * S, top * S), name, font=NAME, fill=t["title"])
    for i, line in enumerate(lines):
        d.text((56 * S, (top + 74 + 30 * i) * S), line, font=BODY, fill=t["tagline"])
    d.rounded_rectangle([PX * S, PY * S, (PX + PW) * S, (PY + PH) * S], radius=10 * S, fill=PANEL, outline=EDGE, width=S)
    for i in range(3):
        cx = (PX + 20 + 18 * i) * S
        d.ellipse([cx - 5 * S, (PY + 18) * S - 5 * S, cx + 5 * S, (PY + 18) * S + 5 * S], fill="#475467")
    return img


def frame(bg, blocks, cursor=None):
    """blocks: [(speaker, lines, colour, font)]; lines may be partially typed."""
    img = bg.copy()
    d = ImageDraw.Draw(img)
    y = PY + 46
    for speaker, lines, colour, fnt in blocks:
        d.text(((PX + 20) * S, y * S), speaker, font=MONO, fill=MUTED)
        for ln in lines:
            d.text(((PX + COL) * S, y * S), ln, font=fnt, fill=colour)
            end = (PX + COL) * S + fnt.getlength(ln)
            y += LINE
        y += 6
    if cursor:
        cy = y - 6 - LINE
        d.rectangle([end + 3 * S, (cy + 2) * S, end + 12 * S, (cy + 20) * S], fill=cursor)
    return img


def typed(lines, n):
    out, left = [], n
    for ln in lines:
        out.append(ln[:left])
        left -= len(ln)
        if left <= 0:
            break
    return out


def main():
    readme = kit_readme()
    rows, blurb = scenes(readme), summary(readme)
    print("summary:", blurb)
    for theme, t in THEMES.items():
        render(rows, theme, base(t, "agentic-kit", blurb))


def render(rows, theme, bg):
    out = PROFILE / f"banner-{theme}.gif"
    width = PW - COL - 24
    frames, durations = [], []
    for ask, runs, came in rows:
        q = wrap(ask, MONO, width * S, 2)
        c = wrap(runs, MONO_B, width * S, 2)
        r = wrap(came, MONO, width * S, 2)
        total = sum(map(len, q))
        for n in range(0, total + 1, 3):
            frames.append(frame(bg, [("you", typed(q, n), WHITE, MONO)], cursor=WHITE)); durations.append(40)
        durations[-1] = 900  # let the question land before Claude answers
        ctotal = sum(map(len, c))
        for n in range(4, ctotal + 4, 4):
            frames.append(frame(bg, [("you", q, WHITE, MONO), ("Claude", typed(c, n), ACCENT, MONO_B)], cursor=ACCENT)); durations.append(30)
        durations[-1] = 1200
        frames.append(frame(bg, [("you", q, WHITE, MONO), ("Claude", c, ACCENT, MONO_B), ("you", r, GREEN, MONO)]))
        # the question and command were read while they typed; hold long enough to read the
        # result (~60 ms a character) plus a 2 s glance back, at least 5 s
        durations.append(max(5000, 2000 + 60 * len(" ".join(r))))
    palette = frames[-1].quantize(colors=48, dither=Image.Dither.NONE)
    pframes = [f.quantize(palette=palette, dither=Image.Dither.NONE) for f in frames]
    pframes[0].save(out, save_all=True, append_images=pframes[1:], duration=durations, loop=0, optimize=True)
    print(f"{len(rows)} scenes, {len(frames)} frames, {sum(durations) / 1000:.1f}s loop, {out.stat().st_size / 1e6:.2f} MB, {theme}")

if __name__ == "__main__":
    main()
