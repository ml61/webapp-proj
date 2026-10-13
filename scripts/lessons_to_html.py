"""Render docs/lessons/*.md to readable HTML in docs/lessons/html/.

Usage:  pip install markdown pygments  &&  python3 scripts/lessons_to_html.py
"""
import pathlib
import re
import markdown
from pygments.formatters import HtmlFormatter

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "docs" / "lessons"
OUT = SRC / "html"

LIGHT = HtmlFormatter(style="friendly").get_style_defs(".codehilite")
DARK = HtmlFormatter(style="github-dark").get_style_defs(".codehilite")

CSS = """
:root { --bg:#ffffff; --fg:#1f2933; --muted:#52606d; --accent:#1d4ed8; --border:#d9e2ec;
        --code-bg:#f3f6f9; --inline:#9d174d; --row:#f8fafc; }
@media (prefers-color-scheme: dark) {
  :root { --bg:#0f141a; --fg:#e4e7eb; --muted:#9aa5b1; --accent:#7aa2ff; --border:#2d3640;
          --code-bg:#161b22; --inline:#f5a3c7; --row:#141a21; }
}
* { box-sizing: border-box; }
body { margin:0; background:var(--bg); color:var(--fg);
       font: 16px/1.65 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
main { max-width: 860px; margin: 0 auto; padding: 32px 16px 80px; }
h1 { font-size: 2rem; line-height:1.25; margin: 0 0 .5em; }
h2 { font-size: 1.45rem; margin: 2em 0 .6em; padding-top:.4em; border-top:1px solid var(--border); }
h3 { font-size: 1.15rem; margin: 1.6em 0 .5em; color: var(--accent); }
a { color: var(--accent); }
hr { display: none; }  /* h2 already draws a separator line */
code { font: .88em/1.5 "SF Mono", Menlo, Consolas, monospace; color: var(--inline);
       background: var(--code-bg); padding: .1em .35em; border-radius: 4px; }
.codehilite { background: var(--code-bg) !important; border:1px solid var(--border); border-radius: 8px;
              padding: 12px 14px; overflow-x: auto; margin: 1em 0; }
.codehilite pre { margin:0; font: 13.5px/1.55 "SF Mono", Menlo, Consolas, monospace; }
.codehilite code { color: inherit; background: none; padding: 0; }
table { border-collapse: collapse; width: 100%; margin: 1em 0; font-size: .92em; display:block; overflow-x:auto; }
th, td { border: 1px solid var(--border); padding: 7px 10px; text-align: left; vertical-align: top; }
th { background: var(--code-bg); }
tr:nth-child(even) td { background: var(--row); }
blockquote { margin: 1em 0; padding: .2em 1em; border-left: 4px solid var(--accent); color: var(--muted); }
li { margin: .25em 0; }
"""

LIST_ITEM = re.compile(r"^\s*([-*+]|\d+\.)\s")


def fix_lists(text):
    """Python-Markdown needs a blank line before a list; GitHub does not. Insert it."""
    out, in_code = [], False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            in_code = not in_code
        prev = out[-1] if out else ""
        if (not in_code and LIST_ITEM.match(line) and prev.strip()
                and not LIST_ITEM.match(prev) and not prev.startswith((" ", "\t"))):
            out.append("")
        out.append(line)
    return "\n".join(out)


def page(title, body):
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>{CSS}
{LIGHT}
@media (prefers-color-scheme: dark) {{ {DARK} }}
</style></head>
<body><main>
{body}
</main></body></html>
"""

def main():
    OUT.mkdir(exist_ok=True)
    for md_file in sorted(SRC.glob("*.md")):
        text = md_file.read_text(encoding="utf-8")
        html = markdown.markdown(fix_lists(text), extensions=["tables", "fenced_code", "codehilite", "sane_lists"],
                                 extension_configs={"codehilite": {"guess_lang": False}})
        title = text.splitlines()[0].lstrip("# ").strip() if text else md_file.stem
        target = OUT / (md_file.stem + ".html")
        target.write_text(page(title, html), encoding="utf-8")
        print("wrote", target.relative_to(ROOT))

if __name__ == "__main__":
    main()
