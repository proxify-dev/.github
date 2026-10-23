"""Write the public README's per-repo images (light + dark SVG) from live repo data.

Each repo gets a strip under its banner, in the same layout. agentic-kit: its GitHub topics
as tags and the ak version from .claude-plugin/marketplace.json.
agentic-playbook: the sections of its docs (### headings under "## Documentation"), its site.
Backgrounds are transparent, so GitHub's own page colour shows through in both themes.

    python3 scripts/org_public.py
"""
import base64
import json
import pathlib
import re
import subprocess
from xml.sax.saxutils import escape

PROFILE = pathlib.Path(__file__).parent.parent / "profile"
ORG = "proxify-dev"
W = 1280
SANS = "Inter, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"
# kit = brand indigo; playbook = green, so the two repos read as two different things
THEMES = {
    "light": dict(fg="#1D2939", muted="#667085", edge="#D0D5DD", chip="#EAECF0", tint=".10", kit="#5258FB", book="#039855", warn="#DC6803"),
    "dark": dict(fg="#F4F5F7", muted="#949BAD", edge="#344054", chip="#262841", tint=".16", kit="#999AFD", book="#12B76A", warn="#F79009"),
}


# GitHub returns topics alphabetically; show the ones we know in this order, any new ones after
KIT_TOPIC_ORDER = ["chat-search", "session-memory", "prompt-inspection", "engineering-skills", "verbatim-web", "account-gateway"]


def tag(topic):
    """chat-search -> Chat search"""
    return topic.replace("-", " ").capitalize()


def gh(path):
    return json.loads(subprocess.run(["gh", "api", path], check=True, capture_output=True, text=True).stdout)


def file(repo, path):
    return base64.b64decode(gh(f"repos/{ORG}/{repo}/contents/{path}")["content"]).decode()


def wrap(text, chars):
    lines, cur = [], ""
    for w in text.split():
        if len(cur) + len(w) + 1 > chars:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    return lines + [cur]


def description(t, desc, x, y):
    if not desc:
        return f'<text x="{x}" y="{y}" font-size="20" font-style="italic" fill="{t["warn"]}">[copy needed: repo description]</text>'
    return "".join(f'<text x="{x}" y="{y + i * 28}" font-size="20" fill="{t["fg"]}">{escape(l)}</text>'
                   for i, l in enumerate(wrap(desc, 100)[:2]))


def chips(t, items, x, y, colour, max_x=900):
    """Tags: tinted fill in the repo's colour, no outline, small radius. Wrap past max_x.
    Returns (svg, bottom y)."""
    out, x0 = "", x
    for c in items:
        w = 22 + 6.6 * len(c)
        if x + w > max_x and x > x0:
            x, y = x0, y + 36
        out += (f'<rect x="{x}" y="{y}" width="{w:.0f}" height="28" rx="6" fill="{colour}" fill-opacity="{t["tint"]}"/>'
                f'<text x="{x + w / 2:.0f}" y="{y + 19}" text-anchor="middle" font-size="13" font-weight="600" fill="{colour}">{escape(c)}</text>')
        x += w + 8
    return out, y + 28


def svg(h, label, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}" role="img" aria-label="{escape(label)}">'
            f'<g font-family="{SANS}">{body}</g></svg>\n')


def strip(t, label, chip_items, meta, cta, colour):
    """Same layout for every repo, under its banner: what it covers as pills on the left,
    the kit's version and the call to action on the right. Stars are left to the live badge below. The banner above carries the summary."""
    pills, bottom = chips(t, chip_items, 8, 16, colour)
    h = max(bottom + 16, 96 if meta else 64)
    return svg(h, label, f'''
      {pills}
      <text x="{W - 8}" y="36" text-anchor="end" font-size="16" fill="{t["muted"]}">{escape(meta)}</text>
      <text x="{W - 8}" y="{70 if meta else 39}" text-anchor="end" font-size="20" font-weight="600" fill="{colour}">{escape(cta)} →</text>''')


def main():
    kit = gh(f"repos/{ORG}/agentic-kit")
    market = json.loads(file("agentic-kit", ".claude-plugin/marketplace.json"))
    ak = next(p["version"] for p in market["plugins"] if p["name"] == "ak")
    # what the kit does, 1-2 words a tag, from the repo's GitHub topics (same source as the
    # topic list on the repo page)
    rank = {t: i for i, t in enumerate(KIT_TOPIC_ORDER)}
    features = [tag(x) for x in sorted(kit["topics"], key=lambda t: rank.get(t, len(rank)))]

    book = gh(f"repos/{ORG}/agentic-playbook")
    docs = file("agentic-playbook", "README.md").split("## Documentation", 1)[1].split("\n## ", 1)[0]
    sections = re.findall(r"^### (.+)$", docs, re.M)
    site = (book["homepage"] or "").removeprefix("https://") or "Read the playbook"

    for theme, t in THEMES.items():
        (PROFILE / f"kit-strip-{theme}.svg").write_text(strip(
            t, "agentic-kit", features, f"ak {ak}", "Install agentic-kit", t["kit"]))
        (PROFILE / f"playbook-strip-{theme}.svg").write_text(strip(
            t, "agentic-playbook", sections, "", f"Open {site}", t["book"]))
    print(f"agentic-kit: tags {features}, ak {ak}")
    print(f"agentic-playbook: sections {sections}, site {site}")


if __name__ == "__main__":
    main()
