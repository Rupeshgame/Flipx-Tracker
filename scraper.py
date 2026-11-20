import csv
import os
import re
from datetime import datetime, timedelta, timezone
from playwright.sync_api import sync_playwright

URL = "https://flipx.in/"
CSV_FILE = "flipx_winners.csv"
IST = timezone(timedelta(hours=5, minutes=30))

def load_existing_rounds():
    saved_rounds = set()
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                saved_rounds.add(row["Round"])
    else:
        with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Round", "Winner", "Recorded_At_IST"])
    return saved_rounds

def fetch_last_winners():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(URL, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(2000)
        text = page.inner_text("body")
        browser.close()

    section = text
    if "Last 5 Winners" in text:
        section = text.split("Last 5 Winners", 1)[1]
        if "Live Bets" in section:
            section = section.split("Live Bets", 1)[0]

    matches = re.findall(
        r"(MARUTI|SPIDER MAN|SUPER MAN|KRRISH)\s+Round\s*#(\d+)",
        section,
        flags=re.IGNORECASE
    )

    if not matches:
        rev_matches = re.findall(
            r"Round\s*#(\d+)\s+(MARUTI|SPIDER MAN|SUPER MAN|KRRISH)",
            section,
            flags=re.IGNORECASE
        )
        matches = [(card, rnd) for rnd, card in rev_matches]

    results = [(int(round_no), card.upper()) for card, round_no in matches]
    results.sort(key=lambda x: x[0])
    return results

def main():
    saved_rounds = load_existing_rounds()
    now = datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")
    winners = fetch_last_winners()

    if not winners:
        print(f"[{now}] Koi winner match nahi hua.")
        return

    new_rows = []
    for round_num, card in winners:
        round_str = f"Round #{round_num}"
        if round_str not in saved_rounds:
            saved_rounds.add(round_str)
            new_rows.append([round_str, card, now])

    if new_rows:
        with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(new_rows)
        for r in new_rows:
            print(f"[{now}] Saved -> {r[0]} : {r[1]}")
    else:
        print(f"[{now}] Koi naya round nahi aaya.")

if __name__ == "__main__":
    main()
