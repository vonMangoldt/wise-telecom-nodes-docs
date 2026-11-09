import os
import re
import sys
import json
import markdown

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "referral-protocol-guide")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(SRC, "referral-protocol-guide.html")
TEMPLATE = sys.argv[3] if len(sys.argv) > 3 else os.path.join(HERE, "guide_template.html")

PAGES = [
    ("overview", "README.md", "Referral Protocol Guide"),
    ("depositors", "for-depositors.md", "For Depositors"),
    ("referrers", "for-referrers.md", "For Referrers"),
    ("integrators", "for-integrators.md", "For Integrators and Partners"),
    ("integration", "ui-integration.md", "UI Integration"),
    ("architecture", "architecture.md", "Architecture for Developers"),
    ("safety", "safety-and-known-findings.md", "Safety and Known Findings"),
    ("addresses", "addresses.md", "Addresses"),
    ("faq", "faq.md", "Frequently Asked Questions"),
]

LINK_MAP = {
    "README.md": "overview",
    "for-depositors.md": "depositors",
    "for-referrers.md": "referrers",
    "for-integrators.md": "integrators",
    "ui-integration.md": "integration",
    "architecture.md": "architecture",
    "safety-and-known-findings.md": "safety",
    "addresses.md": "addresses",
    "faq.md": "faq",
}


def render(token, path):
    text = open(f"{SRC}/{path}", encoding="utf-8").read()
    md = markdown.Markdown(extensions=["tables", "fenced_code", "toc"], extension_configs={"toc": {"toc_depth": "2-3"}})
    html = md.convert(text)
    html = re.sub(r'id="([^"]+)"', lambda m: f'id="{token}-{m.group(1)}"', html)
    for name, tok in LINK_MAP.items():
        html = re.sub(
            r'href="' + re.escape(name) + r'(?:#([^"]+))?"',
            lambda m: f'href="#{tok}" data-page="{tok}"' + (f' data-section="{tok}-{m.group(1)}"' if m.group(1) else ""),
            html,
        )
    html = html.replace("<table>", '<div class="tbl"><table>').replace("</table>", "</table></div>")
    html = re.sub(r'<a href="(https?://[^"]*)"', r'<a href="\1" target="_blank" rel="noopener"', html)
    sections = []
    for item in md.toc_tokens:
        if item["level"] == 1:
            for child in item.get("children", []):
                if child["level"] == 2:
                    sections.append({"id": f"{token}-{child['id']}", "name": child["name"]})
        elif item["level"] == 2:
            sections.append({"id": f"{token}-{item['id']}", "name": item["name"]})
    html = re.sub(r"<h1[^>]*>.*?</h1>", "", html, count=1, flags=re.S)
    return html, sections


pages = []
for token, path, title in PAGES:
    html, sections = render(token, path)
    pages.append({"token": token, "title": title, "html": html, "sections": sections})

nav_json = json.dumps([{"token": p["token"], "title": p["title"], "sections": p["sections"]} for p in pages])

articles = "\n".join(
    f'<article class="page" id="page-{p["token"]}" data-token="{p["token"]}" hidden>\n<h1>{p["title"]}</h1>\n{p["html"]}\n</article>'
    for p in pages
)

template = open(TEMPLATE, encoding="utf-8").read()
out = template.replace("%%NAV_JSON%%", nav_json).replace("%%ARTICLES%%", articles)
open(OUT, "w", encoding="utf-8").write(out)
print("wrote", OUT, len(out), "bytes")
