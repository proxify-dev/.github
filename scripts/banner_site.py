"""Render the agentic-playbook banner: the site's own title and subtitle beside a live
screenshot of agentic.proxify.io, in the same frame as the agentic-kit banner.

Title, subtitle and screenshot are all read from the site on each run; the light banner
shows the site in its light theme and the dark banner in its dark theme.
Needs Google Chrome (headless) for the screenshot; set $CHROME if it is not on PATH.

    uv run --with pillow python3 scripts/banner_site.py
"""
import html
import os
import shutil
import pathlib
import re
import subprocess
import tempfile
import urllib.request

from PIL import Image, ImageChops, ImageDraw

from banner_gif import MATTE_DARK, MONO, NAME, BODY, PROFILE, S, H, W, wrap

SITE = "https://agentic.proxify.io"
CHROME = (os.environ.get("CHROME") or shutil.which("google-chrome") or shutil.which("chromium")
          or "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
# green, so the playbook reads as a different thing from the indigo kit
THEMES = {
    "dark": dict(bg=MATTE_DARK, transparent=True, dot="#054F31", title="#FFFFFF", tagline="#D5D5FE"),
    "light": dict(bg="#FFFFFF", transparent=False, dot="#A6F4C5", title="#15172F", tagline="#475467"),
}
FRAME, EDGE, MUTED, URL_BG = "#1D2939", "#344054", "#949BAD", "#262841"
FX, FY, FW, FH, BAR = 600, 40, 640, 240, 32  # browser frame, 1x units


def heading():
    page = urllib.request.urlopen(SITE).read().decode()
    m = re.search(r'id="page-title"[^>]*>([^<]*)</h1>\s*(?:<[^>]+>\s*)*([^<]+)<', page)
    return html.unescape(m.group(1)).strip(), html.unescape(m.group(2)).strip()


def screenshot(theme):
    """The site follows the browser's colour scheme, so take one capture per banner theme."""
    out = pathlib.Path(tempfile.mkdtemp()) / "site.png"
    scheme = ["--force-dark-mode", "--blink-settings=preferredColorScheme=0"] if theme == "dark" else ["--blink-settings=preferredColorScheme=1"]
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=2", *scheme,
                    "--window-size=1440,900", "--virtual-time-budget=8000", f"--screenshot={out}", SITE],
                   check=True, capture_output=True)
    return Image.open(out).convert("RGB")


def render(theme, t, title, subtitle, shot):
    img = Image.new("RGB", (W, H), t["bg"])
    d = ImageDraw.Draw(img)
    for x in range(560 * S, W, 24 * S):
        for y in range(8 * S, H - 8 * S, 24 * S):
            d.ellipse([x, y, x + 2.4 * S, y + 2.4 * S], fill=t["dot"])
    lines = wrap(subtitle, BODY, 470 * S, 4)
    top = (H / S - (64 + 30 * len(lines))) / 2
    d.text((56 * S, top * S), "agentic-playbook", font=NAME, fill=t["title"])
    for i, line in enumerate(lines):
        d.text((56 * S, (top + 74 + 30 * i) * S), line, font=BODY, fill=t["tagline"])

    d.rounded_rectangle([FX * S, FY * S, (FX + FW) * S, (FY + FH) * S], radius=10 * S, fill=FRAME, outline=EDGE, width=S)
    for i in range(3):
        cx, cy = (FX + 20 + 18 * i) * S, (FY + BAR / 2) * S
        d.ellipse([cx - 5 * S, cy - 5 * S, cx + 5 * S, cy + 5 * S], fill="#475467")
    d.rounded_rectangle([(FX + 220) * S, (FY + 7) * S, (FX + 420) * S, (FY + 25) * S], radius=9 * S, fill=URL_BG)
    d.text(((FX + 320) * S, (FY + 16) * S), SITE.removeprefix("https://"), font=MONO.font_variant(size=12 * S), fill=MUTED, anchor="mm")

    inner_w, inner_h = (FW - 2) * S, (FH - BAR - 1) * S
    crop = shot.crop((0, 0, shot.width, int(shot.width * inner_h / inner_w)))
    img.paste(crop.resize((inner_w, inner_h), Image.LANCZOS), ((FX + 1) * S, (FY + BAR) * S))
    if t["transparent"]:
        # matte pixels outside the browser frame become transparent; the screenshot keeps its own
        diff = ImageChops.difference(img, Image.new("RGB", img.size, t["bg"])).convert("L")
        alpha = diff.point(lambda v: 0 if v == 0 else 255)
        alpha.paste(255, ((FX - 2) * S, (FY - 2) * S, (FX + FW + 2) * S, (FY + FH + 2) * S))
        img = img.convert("RGBA")
        img.putalpha(alpha)
    out = PROFILE / f"playbook-banner-{theme}.png"
    img.save(out, optimize=True)
    return out


def main():
    title, subtitle = heading()
    for theme, t in THEMES.items():
        out = render(theme, t, title, subtitle, screenshot(theme))
        print(f"{out.name}: '{title}', {out.stat().st_size / 1e3:.0f} kB")


if __name__ == "__main__":
    main()
