import datetime
import json
import os
import sys
import urllib.request

TOKEN = os.environ.get("GITHUB_TOKEN", "")
USER = os.environ.get("GITHUB_USERNAME") or "SantiSabio"
OUTPUT = sys.argv[1] if len(sys.argv) > 1 else "cards/github-stats.svg"

COLORS = {
    "bg": "#1a1b27",
    "stroke": "#3b4261",
    "title": "#70a5fd",
    "label": "#38bdae",
    "value": "#bf91f3",
    "muted": "#565f89",
}

OCTOCAT_PATH = (
    "M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 "
    "0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13"
    "-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66"
    ".07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15"
    "-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 "
    "1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 "
    "1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 "
    "1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"
)

MESES = ["ene", "feb", "mar", "abr", "may", "jun",
         "jul", "ago", "sep", "oct", "nov", "dic"]


def api(path):
    req = urllib.request.Request(
        f"https://api.github.com{path}",
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "github-stats-card",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as res:
        return json.load(res)


def safe(fn):
    try:
        return fn()
    except Exception as exc:
        print(f"aviso: {exc}", file=sys.stderr)
        return None


def total_stars():
    stars, page = 0, 1
    while True:
        repos = api(f"/users/{USER}/repos?per_page=100&page={page}")
        stars += sum(r["stargazers_count"] for r in repos)
        if len(repos) < 100:
            return stars
        page += 1


def search_total(query):
    data = api(f"/search/commits?q={query}&per_page=1")
    return data["total_count"]


def search_issues_total(query):
    data = api(f"/search/issues?q={query}&per_page=1")
    return data["total_count"]


def contributed_repos():
    names, page = set(), 1
    while True:
        if page > 10:
            break
        data = api(
            f"/search/commits?q=author:{USER}+is:public&per_page=100&page={page}"
        )
        items = data["items"]
        names.update(i["repository"]["full_name"] for i in items)
        if len(items) < 100:
            break
        page += 1
    return len(names)


def fmt(n):
    return str(n) if n is not None else "--"


def build_svg(stats):
    rows = [
        ("Estrellas ganadas", stats["stars"]),
        ("Commits totales", stats["commits"]),
        ("Pull requests", stats["prs"]),
        ("Issues creados", stats["issues"]),
        ("Repos con contribuciones", stats["contributed"]),
    ]
    today = datetime.date.today()
    fecha = f"{today.day} {MESES[today.month - 1]} {today.year}"
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="340" height="200" viewBox="0 0 340 200">',
        "<style>* { font-family: 'Segoe UI', Ubuntu, 'Helvetica Neue', Sans-Serif; }</style>",
        f'<rect x="0.5" y="0.5" width="339" height="199" rx="5" fill="{COLORS["bg"]}" stroke="{COLORS["stroke"]}" stroke-opacity="0.6"/>',
        f'<text x="30" y="40" font-size="22" fill="{COLORS["title"]}" font-weight="600">Estad\u00edsticas de GitHub</text>',
        f'<g transform="translate(289,17) scale(1.5)" fill="{COLORS["muted"]}"><path d="{OCTOCAT_PATH}"/></g>',
    ]
    y = 74
    for label, value in rows:
        parts.append(
            f'<text x="30" y="{y}" font-size="14" fill="{COLORS["label"]}">{label}:</text>'
            f'<text x="310" y="{y}" font-size="14" fill="{COLORS["value"]}" text-anchor="end" font-weight="600">{fmt(value)}</text>'
        )
        y += 23
    parts.append(
        f'<text x="30" y="186" font-size="10" fill="{COLORS["muted"]}">Hist\u00f3rico completo \u00b7 actualizado el {fecha}</text>'
    )
    parts.append("</svg>")
    return "\n".join(parts)


def main():
    if not TOKEN:
        print("GITHUB_TOKEN no definido", file=sys.stderr)
        sys.exit(1)
    stats = {
        "stars": safe(total_stars),
        "commits": safe(lambda: search_total(f"author:{USER}+is:public")),
        "prs": safe(lambda: search_issues_total(f"author:{USER}+is:pr+is:public")),
        "issues": safe(lambda: search_issues_total(f"author:{USER}+is:issue+is:public")),
        "contributed": safe(contributed_repos),
    }
    svg = build_svg(stats)
    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as fh:
        fh.write(svg)
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
