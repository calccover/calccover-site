import csv, re, requests
from bs4 import BeautifulSoup

def find_emails(domain):
    emails = set()
    # Try common contact pages
    urls_to_try = [
        f"https://{domain}/contact",
        f"https://{domain}/about",
        f"https://{domain}/write-for-us",
        f"https://{domain}/contribute"
    ]
    
    for url in urls_to_try:
        try:
            r = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            soup = BeautifulSoup(r.text, "html.parser")
            text = soup.get_text()
            # Regex for emails
            found = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
            emails.update(found)
        except Exception:
            pass
    return list(emails)

# Read targets, find emails, update CSV
with open("scripts/outreach/data/targets.csv", "r") as f:
    reader = csv.DictReader(f)
    rows = list(reader)

for row in rows:
    if not row.get("Contact Email") or row["Contact Email"] == "contact form":
        emails = find_emails(row["Target Site"])
        if emails:
            row["Contact Email"] = emails[0]  # Use the first found
            print(f"Found {emails[0]} for {row['Target Site']}")

with open("scripts/outreach/data/targets.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)