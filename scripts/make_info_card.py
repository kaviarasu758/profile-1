#!/usr/bin/env python3
"""
make_info_card.py
Generates a neofetch-style system info card SVG (info-card.svg)
with staggered slide-and-fade animation for role, stack, and highlights.
"""

import os
import argparse

DEFAULT_CONFIG = {
    "user": "kaviarasu758",
    "host": "github",
    "os": "Arch Linux x86_64",
    "kernel": "Linux 6.9.3-hardened",
    "uptime": "24/7 Building",
    "shell": "zsh 5.9",
    "role": "Full Stack Engineer & OSS Contributor",
    "stack": "TypeScript, Python, Go, React, Next.js, Node.js",
    "databases": "PostgreSQL, Redis, MongoDB",
    "devops": "Docker, Kubernetes, GitHub Actions, AWS",
    "focus": "High-performance Web Apps & Interactive Visuals",
    "status": "Available for high-impact projects"
}

def generate_info_card(data: dict, output_path: str = "info-card.svg", static: bool = False):
    svg_width = 490
    svg_height = 420
    
    fields = [
        ("OS", data.get("os", "Arch Linux")),
        ("Kernel", data.get("kernel", "Linux 6.9")),
        ("Uptime", data.get("uptime", "Always up")),
        ("Shell", data.get("shell", "zsh")),
        ("Role", data.get("role", "Software Engineer")),
        ("Stack", data.get("stack", "Python, TS, Go")),
        ("Databases", data.get("databases", "Postgres, Redis")),
        ("DevOps", data.get("devops", "Docker, K8s, CI/CD")),
        ("Focus", data.get("focus", "Building cool things")),
        ("Status", data.get("status", "Exploring new horizons")),
    ]

    header_user = f"{data.get('user', 'developer')}@{data.get('host', 'github')}"
    divider = "—" * 38

    # Build rows with staggered CSS delays
    rows_svg = []
    base_y = 75
    line_spacing = 26
    
    # Header line (user@host)
    rows_svg.append(f"""
    <g class="row" style="animation-delay: 0.05s;">
      <text x="25" y="{base_y}" class="user-host">{header_user}</text>
    </g>
    <g class="row" style="animation-delay: 0.10s;">
      <text x="25" y="{base_y + 14}" class="divider">{divider}</text>
    </g>
    """)

    current_y = base_y + 36
    delay = 0.15

    for label, val in fields:
        delay += 0.06
        rows_svg.append(f"""
    <g class="row" style="animation-delay: {delay:.2f}s;">
      <text x="25" y="{current_y}" class="key">{label}:</text>
      <text x="115" y="{current_y}" class="value">{val}</text>
    </g>""")
        current_y += line_spacing

    # Color palettes bar (neofetch color blocks)
    delay += 0.08
    color_blocks = ["#ff5f56", "#ffbd2e", "#27c93f", "#58a6ff", "#bc8cff", "#39d353", "#f0883e", "#79c0ff"]
    palette_rects = []
    for i, c in enumerate(color_blocks):
        palette_rects.append(f'<rect x="{25 + i * 22}" y="{current_y + 6}" width="18" height="10" rx="2" fill="{c}" />')

    rows_svg.append(f"""
    <g class="row" style="animation-delay: {delay:.2f}s;">
      {''.join(palette_rects)}
    </g>""")

    animation_css = """
      @keyframes lineSlide {
        0% {
          opacity: 0;
          transform: translateX(-12px);
        }
        100% {
          opacity: 1;
          transform: translateX(0);
        }
      }
      .row {
        animation: lineSlide 0.4s cubic-bezier(0.16, 1, 0.3, 1) backwards;
      }
    """ if not static else ""

    svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_width} {svg_height}" width="100%" height="100%">
  <defs>
    <style>
      .bg {{ fill: #0d1117; }}
      .border {{ stroke: #30363d; stroke-width: 1; fill: none; }}
      .title-text {{ fill: #58a6ff; font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace; font-size: 12px; font-weight: 600; }}
      .user-host {{ fill: #58a6ff; font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace; font-size: 14px; font-weight: 700; }}
      .divider {{ fill: #30363d; font-family: monospace; font-size: 12px; }}
      .key {{ fill: #ff7b72; font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace; font-size: 12px; font-weight: 600; }}
      .value {{ fill: #c9d1d9; font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace; font-size: 12px; }}
      {animation_css}
    </style>
  </defs>

  <!-- Background Card -->
  <rect width="{svg_width}" height="{svg_height}" rx="8" class="bg" />
  <rect width="{svg_width - 1}" height="{svg_height - 1}" x="0.5" y="0.5" rx="8" class="border" />

  <!-- Terminal Header -->
  <circle cx="18" cy="18" r="4.5" fill="#ff5f56" />
  <circle cx="32" cy="18" r="4.5" fill="#ffbd2e" />
  <circle cx="46" cy="18" r="4.5" fill="#27c93f" />
  <text x="65" y="22" class="title-text">neofetch --profile</text>

  <!-- Content Rows -->
  {''.join(rows_svg)}
</svg>
"""

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(svg_content)
    print(f"Generated info card SVG: {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Generate neofetch-style info card SVG.")
    parser.add_argument("--output", "-o", default="info-card.svg", help="Output SVG path")
    parser.add_argument("--user", default="developer", help="User name in card header")
    parser.add_argument("--role", default="Full Stack Engineer & OSS Contributor", help="Role text")
    parser.add_argument("--stack", default="TypeScript, Python, Go, React, Next.js", help="Tech stack")
    parser.add_argument("--static", action="store_true", help="Disable animations")
    args = parser.parse_args()

    static_mode = args.static or os.environ.get("STATIC", "0") == "1"
    config = DEFAULT_CONFIG.copy()
    if args.user:
        config["user"] = args.user
    if args.role:
        config["role"] = args.role
    if args.stack:
        config["stack"] = args.stack

    generate_info_card(config, args.output, static=static_mode)

if __name__ == "__main__":
    main()
