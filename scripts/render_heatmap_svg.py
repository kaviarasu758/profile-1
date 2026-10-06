#!/usr/bin/env python3
"""
render_heatmap_svg.py
Renders data/contributions.json into an animated SVG contribution heatmap (contrib-heatmap.svg)
with a diagonal slide-down reveal animation, stats footer, and legend.
"""

import sys
import os
import json
import argparse
from datetime import datetime

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]

MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
DAY_LABELS = ["", "Mon", "", "Wed", "", "Fri", ""]

def generate_svg(data: dict, output_path: str, static: bool = False):
    days = data.get("days", [])
    stats = data.get("stats", {})
    total_count = stats.get("totalContributions", 0)
    current_streak = stats.get("currentStreak", 0)
    longest_streak = stats.get("longestStreak", 0)

    # Layout geometry
    box_size = 11
    box_gap = 3.5
    step = box_size + box_gap
    start_x = 35
    start_y = 48
    
    # Calculate grid (up to 53 weeks x 7 days)
    # GitHub days list is chronological. We map by week index (0..52) and weekday (0..6, Sunday=0)
    # To align correctly, let's group by weeks.
    weeks = []
    current_week = []
    
    if days:
        first_date = datetime.strptime(days[0]["date"], "%Y-%m-%d")
        # In GitHub calendar: Sunday is day 0, Saturday is 6
        first_weekday = (first_date.weekday() + 1) % 7 # Python weekday(): Mon=0..Sun=6 -> Sun=0, Mon=1...
        
        # Pad first week if it starts mid-week
        for _ in range(first_weekday):
            current_week.append(None)
            
        for d in days:
            current_week.append(d)
            if len(current_week) == 7:
                weeks.append(current_week)
                current_week = []
        if current_week:
            while len(current_week) < 7:
                current_week.append(None)
            weeks.append(current_week)
            
    # Keep only the last 53 weeks
    if len(weeks) > 53:
        weeks = weeks[-53:]
    elif len(weeks) < 53:
        # Pad leading empty weeks
        needed = 53 - len(weeks)
        weeks = [[None]*7 for _ in range(needed)] + weeks

    # Month labels positioning
    month_positions = []
    last_month = None
    for w_idx, week in enumerate(weeks):
        for d in week:
            if d:
                m = int(d["date"].split("-")[1])
                if m != last_month:
                    month_positions.append((w_idx * step + start_x, MONTH_NAMES[m - 1]))
                    last_month = m
                break

    # SVG Canvas dimensions
    svg_width = 860
    svg_height = 200

    # Build SVG cells
    rects_svg = []
    for col_idx, week in enumerate(weeks):
        for row_idx, d in enumerate(week):
            if not d:
                continue
            x = start_x + col_idx * step
            y = start_y + row_idx * step
            
            level = d.get("level", 0)
            if level >= len(PALETTE):
                level = len(PALETTE) - 1
            color = PALETTE[level]
            
            # Diagonal animation stagger: delay based on (col + row)
            delay = (col_idx * 0.02) + (row_idx * 0.03)
            cell_class = "cell"
            
            tooltip = f"{d['count']} contributions on {d['date']}"
            rects_svg.append(
                f'<rect class="{cell_class}" x="{x:.1f}" y="{y:.1f}" width="{box_size}" height="{box_size}" '
                f'rx="2.5" ry="2.5" fill="{color}" style="animation-delay: {delay:.3f}s;"><title>{tooltip}</title></rect>'
            )

    # Build Month Labels SVG
    month_labels_svg = []
    for mx, mname in month_positions:
        month_labels_svg.append(f'<text x="{mx:.1f}" y="36" class="label-text">{mname}</text>')

    # Build Day Labels SVG (Mon, Wed, Fri)
    day_labels_svg = []
    for r_idx, label in enumerate(DAY_LABELS):
        if label:
            dy = start_y + r_idx * step + 9
            day_labels_svg.append(f'<text x="12" y="{dy:.1f}" class="label-text">{label}</text>')

    # Build Legend SVG
    legend_start_x = svg_width - 150
    legend_y = svg_height - 25
    legend_rects = []
    for idx, c in enumerate(PALETTE):
        lx = legend_start_x + 32 + idx * 14
        legend_rects.append(f'<rect x="{lx}" y="{legend_y - 9}" width="10" height="10" rx="2" fill="{c}" />')

    # Animation CSS
    animation_css = """
      @keyframes diagonalSlide {
        0% {
          opacity: 0;
          transform: translateY(-8px) scale(0.85);
        }
        70% {
          opacity: 1;
          transform: translateY(1px) scale(1.02);
        }
        100% {
          opacity: 1;
          transform: translateY(0) scale(1);
        }
      }
      .cell {
        animation: diagonalSlide 0.45s cubic-bezier(0.16, 1, 0.3, 1) backwards;
        transform-origin: center;
      }
    """ if not static else ""

    svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_width} {svg_height}" width="100%" height="100%">
  <defs>
    <style>
      .bg {{ fill: #0d1117; }}
      .border {{ stroke: #30363d; stroke-width: 1; fill: none; }}
      .title-text {{ fill: #58a6ff; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", monospace; font-size: 13px; font-weight: 600; }}
      .label-text {{ fill: #8b949e; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, monospace; font-size: 10px; }}
      .stat-text {{ fill: #c9d1d9; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, monospace; font-size: 11px; }}
      .stat-bold {{ fill: #58a6ff; font-weight: 600; }}
      .legend-text {{ fill: #8b949e; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, monospace; font-size: 10px; }}
      {animation_css}
    </style>
  </defs>

  <!-- Background Card -->
  <rect width="{svg_width}" height="{svg_height}" rx="8" class="bg" />
  <rect width="{svg_width - 1}" height="{svg_height - 1}" x="0.5" y="0.5" rx="8" class="border" />

  <!-- Title & Controls -->
  <circle cx="18" cy="18" r="4.5" fill="#ff5f56" />
  <circle cx="32" cy="18" r="4.5" fill="#ffbd2e" />
  <circle cx="46" cy="18" r="4.5" fill="#27c93f" />
  <text x="65" y="22" class="title-text">git contribution-matrix --live</text>

  <!-- Month Labels -->
  {''.join(month_labels_svg)}

  <!-- Weekday Labels -->
  {''.join(day_labels_svg)}

  <!-- Grid Cells -->
  <g id="cells">
    {''.join(rects_svg)}
  </g>

  <!-- Stats & Footer -->
  <text x="35" y="{legend_y}" class="stat-text">
    <tspan class="stat-bold">{total_count:,}</tspan> contributions in the last year
    <tspan fill="#484f58"> • </tspan>
    Current Streak: <tspan class="stat-bold">{current_streak}d</tspan>
    <tspan fill="#484f58"> • </tspan>
    Longest: <tspan class="stat-bold">{longest_streak}d</tspan>
  </text>

  <!-- Legend -->
  <text x="{legend_start_x}" y="{legend_y}" class="legend-text">Less</text>
  {''.join(legend_rects)}
  <text x="{legend_start_x + 122}" y="{legend_y}" class="legend-text">More</text>
</svg>
"""

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(svg_content)
    print(f"Generated heatmap SVG: {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Render animated GitHub contribution calendar SVG.")
    parser.add_argument("--input", "-i", default="data/contributions.json", help="Input contributions JSON")
    parser.add_argument("--output", "-o", default="contrib-heatmap.svg", help="Output SVG path")
    parser.add_argument("--static", action="store_true", help="Disable animation (frozen frame)")
    args = parser.parse_args()

    static_mode = args.static or os.environ.get("STATIC", "0") == "1"

    if not os.path.exists(args.input):
        print(f"Input file not found: {args.input}. Generating sample/empty grid.")
        sample_data = {
            "days": [],
            "stats": {"totalContributions": 0, "currentStreak": 0, "longestStreak": 0}
        }
        generate_svg(sample_data, args.output, static=static_mode)
    else:
        with open(args.input, "r", encoding="utf-8") as f:
            data = json.load(f)
        generate_svg(data, args.output, static=static_mode)

if __name__ == "__main__":
    main()
