#!/usr/bin/env python3
"""
fetch_contributions.py
Fetches the public GitHub contribution calendar for a given username without needing any GitHub API token.
Saves parsed data and derived statistics to data/contributions.json.
"""

import sys
import os
import json
import re
import argparse
from datetime import datetime, timedelta, timezone
import requests
from bs4 import BeautifulSoup

DEFAULT_USERNAME = os.environ.get("GITHUB_USERNAME", "kaviarasu758")

def fetch_contribution_html(username: str) -> str:
    url = f"https://github.com/users/{username}/contributions"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }
    response = requests.get(url, headers=headers, timeout=15)
    if response.status_code != 200:
        raise RuntimeError(f"Failed to fetch contributions for user '{username}'. HTTP status {response.status_code}")
    return response.text

def parse_contributions(html_text: str):
    soup = BeautifulSoup(html_text, "html.parser")
    
    # Extract tooltips if present (GitHub uses tooltips for exact counts: "X contributions on Month Day, Year" or "No contributions on ...")
    tooltips = {}
    for tip in soup.find_all(["tool-tip", "div"], attrs={"for": True}):
        target_id = tip.get("for")
        text = tip.get_text(strip=True)
        if target_id and text:
            tooltips[target_id] = text

    days_data = []
    # Find all day cells
    day_elements = soup.find_all("td", class_=re.compile(r"ContributionCalendar-day"))
    if not day_elements:
        # Fallback for SVG rect format in older/alternate layouts
        day_elements = soup.find_all("rect", attrs={"data-date": True})

    for el in day_elements:
        date_str = el.get("data-date")
        if not date_str:
            continue
        
        level = el.get("data-level", "0")
        try:
            level = int(level)
        except ValueError:
            level = 0
            
        el_id = el.get("id", "")
        count = 0
        tooltip_text = tooltips.get(el_id, "")
        
        # Try to parse count from tooltip or text inside element
        if tooltip_text:
            match = re.search(r"(\d+)\s+contribution", tooltip_text)
            if match:
                count = int(match.group(1))
            elif "No contributions" in tooltip_text or "0 contribution" in tooltip_text:
                count = 0
        else:
            # Check text content or data attributes
            text = el.get_text(strip=True)
            match = re.search(r"(\d+)\s+contribution", text)
            if match:
                count = int(match.group(1))
            else:
                # Level heuristic if exact count not available
                level_to_count = {0: 0, 1: 1, 2: 4, 3: 8, 4: 15}
                count = level_to_count.get(level, 0)

        days_data.append({
            "date": date_str,
            "count": count,
            "level": level
        })

    # Sort days by date
    days_data.sort(key=lambda x: x["date"])
    
    # Calculate statistics
    total_contributions = sum(d["count"] for d in days_data)
    
    current_streak = 0
    longest_streak = 0
    temp_streak = 0
    best_day = {"date": "", "count": 0}
    
    # Today's date check for current streak
    today_str = datetime.now().strftime("%Y-%m-%d")
    yesterday_str = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    for d in days_data:
        cnt = d["count"]
        if cnt > best_day["count"]:
            best_day = {"date": d["date"], "count": cnt}
            
        if cnt > 0:
            temp_streak += 1
            if temp_streak > longest_streak:
                longest_streak = temp_streak
        else:
            temp_streak = 0

    # Calculate current active streak backwards from latest day
    for d in reversed(days_data):
        if d["date"] > today_str:
            continue
        if d["count"] > 0:
            current_streak += 1
        elif d["date"] == today_str:
            # If today has 0 yet, streak can still be alive from yesterday
            continue
        else:
            break

    # Monthly aggregates
    monthly_totals = {}
    for d in days_data:
        month_key = d["date"][:7] # YYYY-MM
        monthly_totals[month_key] = monthly_totals.get(month_key, 0) + d["count"]

    return {
        "days": days_data,
        "stats": {
            "totalContributions": total_contributions,
            "currentStreak": current_streak,
            "longestStreak": longest_streak,
            "bestDay": best_day,
            "monthlyTotals": monthly_totals,
            "updatedAt": datetime.now(timezone.utc).isoformat()
        }
    }

def main():
    parser = argparse.ArgumentParser(description="Fetch GitHub contribution calendar data.")
    parser.add_argument("--username", "-u", default=DEFAULT_USERNAME, help="GitHub username")
    parser.add_argument("--output", "-o", default="data/contributions.json", help="Output JSON path")
    args = parser.parse_args()

    print(f"Fetching contribution data for user: {args.username}...")
    try:
        html = fetch_contribution_html(args.username)
        data = parse_contributions(html)
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
        
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            
        print(f"Successfully saved {len(data['days'])} days of contributions to {args.output}")
        print(f"Total: {data['stats']['totalContributions']} | Current Streak: {data['stats']['currentStreak']}d | Longest Streak: {data['stats']['longestStreak']}d")
    except Exception as e:
        print(f"Error fetching contributions: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
