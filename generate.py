"""Build the neofetch-style profile card (dark_mode.svg / light_mode.svg).

Run locally or from the daily GitHub Action:  GITHUB_TOKEN=... python generate.py
Only uses the Python standard library.
"""

import datetime as dt
import json
import os
import urllib.request
from xml.sax.saxutils import escape

USER = "harshvats2000"
BIRTHDAY = dt.date(2000, 10, 21)
WIDTH = 60  # characters in the info column

THEMES = {
    "dark_mode.svg": {
        "bg": "#161b22", "text": "#c9d1d9", "key": "#ffa657",
        "value": "#a5d6ff", "cc": "#616e7f", "border": "#30363d",
    },
    "light_mode.svg": {
        "bg": "#f6f8fa", "text": "#24292f", "key": "#953800",
        "value": "#0a3069", "cc": "#c2cfde", "border": "#d0d7de",
    },
}


def uptime(today):
    years = today.year - BIRTHDAY.year
    months = today.month - BIRTHDAY.month
    days = today.day - BIRTHDAY.day
    if days < 0:
        months -= 1
        prev_month_end = today.replace(day=1) - dt.timedelta(days=1)
        days += prev_month_end.day
    if months < 0:
        years -= 1
        months += 12
    plural = lambda n, w: f"{n} {w}{'' if n == 1 else 's'}"
    return f"{plural(years, 'year')}, {plural(months, 'month')}, {plural(days, 'day')}"


def graphql(query):
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise SystemExit("GITHUB_TOKEN is required")
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query}).encode(),
        headers={"Authorization": f"bearer {token}", "User-Agent": USER},
    )
    with urllib.request.urlopen(req) as resp:
        body = json.load(resp)
    if "errors" in body:
        raise SystemExit(body["errors"])
    return body["data"]


def github_stats(today):
    created = graphql(f'{{user(login:"{USER}"){{createdAt followers{{totalCount}}}}}}')["user"]
    first_year = int(created["createdAt"][:4])
    parts = []
    for year in range(first_year, today.year + 1):
        parts.append(
            f'y{year}: contributionsCollection(from:"{year}-01-01T00:00:00Z", to:"{year}-12-31T23:59:59Z")'
            "{contributionCalendar{totalContributions}}"
        )
    years = graphql(f'{{user(login:"{USER}"){{{" ".join(parts)}}}}}')["user"]
    per_year = {int(k[1:]): v["contributionCalendar"]["totalContributions"] for k, v in years.items()}
    since = dt.datetime.strptime(created["createdAt"][:10], "%Y-%m-%d").strftime("%b %Y")
    return {
        "total": sum(per_year.values()),
        "this_year": per_year.get(today.year, 0),
        "followers": created["followers"]["totalCount"],
        "since": since,
    }


# Each info line is a list of (css class, text) segments so it can be coloured.
def kv(key, value, width=WIDTH):
    dots = width - len(". ") - len(key) - len(": ") - len(value) - 1
    return [("cc", ". "), ("key", key), ("cc", ": " + "." * max(dots, 1) + " "), ("value", value)]


def kv2(left, right):
    half = (WIDTH - 3) // 2
    return kv(*left, width=half) + [("cc", " | ")] + kv(*right, width=WIDTH - half - 3 + 2)[1:]


def header(title):
    return [("text", title + " "), ("cc", "-" * (WIDTH - len(title) - 1))]


def section(title):
    return [("cc", "- "), ("text", title + " "), ("cc", "-" * (WIDTH - len(title) - 3))]


BLANK = [("cc", ".")]


def info_lines(today, stats):
    fmt = lambda n: f"{n:,}"
    return [
        header("harsh@vats"),
        kv("OS", "macOS, iOS, Web"),
        kv("Uptime", uptime(today)),
        kv("Host", "India"),
        kv("Kernel", "Technical AI Engineer"),
        kv("IDE", "Claude Code"),
        BLANK,
        kv("AI.Workflow", "Claude Code, AI coding agents"),
        kv("AI.Building", "LLM features, OpenAI API, Document AI"),
        kv("Languages", "TypeScript, Python, C#, Swift"),
        kv("Stack.Web", "React, Next.js, Node.js, NestJS"),
        kv("Stack.Data", "PostgreSQL, MySQL, MongoDB"),
        kv("Stack.Cloud", "Vercel, GCP, AWS"),
        BLANK,
        kv("Projects", "WOYM, NewsGamer, Stacks"),
        BLANK,
        section("Contact"),
        kv("Website", "hvats.in"),
        kv("LinkedIn", "harsh-vats-02b210150"),
        kv("GitHub", USER),
        BLANK,
        section("GitHub Stats"),
        kv2(("Contributions", fmt(stats["total"])), ("Followers", fmt(stats["followers"]))),
        kv2(("This year", fmt(stats["this_year"])), ("Since", stats["since"])),
    ]


def render(theme, ascii_lines, lines):
    font_size, line_h, char_w, pad = 16, 20, 9.7, 22
    # the portrait uses small type so it can carry more detail
    a_font, a_line, a_char_w = 6, 7, 3.62
    ascii_cols = max(len(l) for l in ascii_lines)
    info_x = pad + ascii_cols * a_char_w + 3 * char_w
    art_h = len(ascii_lines) * a_line
    info_h = len(lines) * line_h
    width = round(info_x + WIDTH * char_w + pad)
    height = round(pad * 2 + max(art_h, info_h))
    t = theme
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, \'Liberation Mono\', monospace" '
        f'width="{width}" height="{height}" viewBox="0 0 {width} {height}" font-size="{font_size}px">',
        "<style>"
        f".key{{fill:{t['key']}}}.value{{fill:{t['value']}}}.cc{{fill:{t['cc']}}}.text{{fill:{t['text']}}}"
        "text,tspan{white-space:pre}"
        "</style>",
        f'<rect width="{width}" height="{height}" rx="15" fill="{t["bg"]}" stroke="{t["border"]}"/>',
    ]
    ay = pad + (height - 2 * pad - art_h) / 2 + a_line - 1
    out.append(f'<text x="{pad}" y="{ay:.1f}" class="text" font-size="{a_font}px" xml:space="preserve">')
    for i, l in enumerate(ascii_lines):
        out.append(f'<tspan x="{pad}" y="{ay + i * a_line:.1f}">{escape(l)}</tspan>')
    out.append("</text>")
    iy = pad + (height - 2 * pad - info_h) / 2 + line_h - 5
    out.append(f'<text x="{info_x:.1f}" y="{iy:.1f}" class="text" xml:space="preserve">')
    for i, segs in enumerate(lines):
        inner = "".join(f'<tspan class="{c}">{escape(s)}</tspan>' for c, s in segs)
        out.append(f'<tspan x="{info_x:.1f}" y="{iy + i * line_h:.1f}">{inner}</tspan>')
    out.append("</text></svg>")
    return "\n".join(out) + "\n"


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    today = dt.date.today()
    lines = info_lines(today, github_stats(today))
    for name, theme in THEMES.items():
        # dark mode uses inverted art: on a dark background, dense characters read as light tones
        art = os.path.join(here, "ascii_dark.txt" if name.startswith("dark") else "ascii_light.txt")
        ascii_lines = open(art).read().rstrip("\n").split("\n")
        with open(os.path.join(here, name), "w") as f:
            f.write(render(theme, ascii_lines, lines))
    print(f"wrote {', '.join(THEMES)}")


if __name__ == "__main__":
    main()
