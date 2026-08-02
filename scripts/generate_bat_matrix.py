"""
Generates bat-matrix.svg: your GitHub contribution history mapped
onto a bat-signal silhouette, colored by real daily activity intensity.

Requires: GITHUB_TOKEN env var (GraphQL read access to public contribution data)
Requires: USERNAME env var
"""
import os
import json
import urllib.request

TOKEN = os.environ["GITHUB_TOKEN"]
USERNAME = os.environ.get("USERNAME", "TarunSinghChauhan")

# Bat silhouette mask, traced from the uploaded logo (22 rows x 52 cols)
MASK_ROWS = ['0000000000000001110000000000000000111000000000000000', '0000000000011111100000001001000000011111100000000000', '0000000001111111100000001111000000011111111000000000', '0000000111111111100000001111000000011111111110000000', '0000011111111111100000011111100000011111111111100000', '0000111111111111111000111111110001111111111111110000', '0001111111111111111111111111111111111111111111111000', '0011111111111111111111111111111111111111111111111100', '0111111111111111111111111111111111111111111111111110', '1110000111111111111111111111111111111111111110000111', '1000000001111111111111111111111111111111111000000001', '0000000000111111111111111111111111111111110000000000', '0000000000111111111111111111111111111111110000000000', '0000000000011111111111111111111111111111100000000000', '0000000000011000000011111111111100000001100000000000', '0000000000000000000000111111110000000000000000000000', '0000000000000000000000011111100000000000000000000000', '0000000000000000000000011111100000000000000000000000', '0000000000000000000000001111000000000000000000000000', '0000000000000000000000000110000000000000000000000000', '0000000000000000000000000110000000000000000000000000', '0000000000000000000000000000000000000000000000000000']

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        weeks {
          contributionDays {
            date
            contributionCount
          }
        }
      }
    }
  }
}
"""

def fetch_contributions():
    body = json.dumps({"query": QUERY, "variables": {"login": USERNAME}}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=body,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req) as resp:
        data = json.load(resp)
    weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    counts = []
    for w in weeks:
        for d in w["contributionDays"]:
            counts.append(d["contributionCount"])
    return counts

def lerp(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))

def build_svg(counts):
    mask = [[c == "1" for c in row] for row in MASK_ROWS]
    rows, cols = len(mask), len(mask[0])
    true_cells = [(r, c) for r in range(rows) for c in range(cols) if mask[r][c]]

    n = len(true_cells)
    if len(counts) >= n:
        values = counts[-n:]
    else:
        reps = (n // len(counts)) + 1
        values = (counts * reps)[:n]

    max_val = max(values) if max(values) > 0 else 1
    low_col = (58, 5, 5)     # deep crimson
    high_col = (239, 68, 68) # bright red

    cell, gap = 20, 3
    pad = 30
    W = cols * (cell + gap) + pad * 2
    H = rows * (cell + gap) + pad * 2 + 50

    svg = [f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">']
    svg.append(f'<rect width="{W}" height="{H}" fill="#0A0608"/>')
    svg.append(
        f'<text x="{pad}" y="28" font-family="Verdana, Arial, sans-serif" '
        f'font-size="16" fill="#EF4444" font-weight="bold">CONTRIBUTION SIGNAL</text>'
    )

    for (r, c), val in zip(true_cells, values):
        t = val / max_val
        col = lerp(low_col, high_col, t)
        x = pad + c * (cell + gap)
        y = pad + 40 + r * (cell + gap)
        hexcol = "#%02x%02x%02x" % col
        svg.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="3" fill="{hexcol}"/>')

    svg.append("</svg>")
    return "\n".join(svg)

if __name__ == "__main__":
    counts = fetch_contributions()
    svg = build_svg(counts)
    with open("bat-matrix.svg", "w") as f:
        f.write(svg)
    print(f"Generated bat-matrix.svg from {len(counts)} days of real contribution data.")
