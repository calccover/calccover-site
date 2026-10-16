#!/usr/bin/env python3
"""
Striking distance analysis — fetches data from Google Search Console API.

Requires GOOGLE_APPLICATION_CREDENTIALS_JSON env var (set by GitHub Actions secret).

Output: striking_distance_report.md
"""
import json
import os
import datetime
import urllib.request
import urllib.parse
import base64
import sys

SITE_URL = "sc-domain:calccover.com"
STRIKING_MIN = 8
STRIKING_MAX = 20
LOOKBACK_DAYS = 28
OUTPUT_FILE = "striking_distance_report.md"


def b64(data):
    return base64.urlsafe_b64encode(data).rstrip(b"=")


def get_access_token(credentials_json):
    """Get an OAuth token from a service account JSON."""
    try:
        creds = json.loads(credentials_json)
    except json.JSONDecodeError as e:
        print(f"ERROR: Could not parse GSC_CREDENTIALS_JSON: {e}")
        sys.exit(1)

    if "client_email" not in creds or "private_key" not in creds:
        print("ERROR: GSC_CREDENTIALS_JSON is missing client_email or private_key")
        print(f"Found keys: {list(creds.keys())}")
        sys.exit(1)

    now = int(datetime.datetime.now().timestamp())
    header = {"alg": "RS256", "typ": "JWT"}
    claim = {
        "iss": creds["client_email"],
        "scope": "https://www.googleapis.com/auth/webmasters.readonly",
        "aud": "https://oauth2.googleapis.com/token",
        "iat": now,
        "exp": now + 3600,
    }

    header_b64 = b64(json.dumps(header).encode())
    claim_b64 = b64(json.dumps(claim).encode())
    signing_input = header_b64 + b"." + claim_b64

    try:
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import padding
        from cryptography.hazmat.backends import default_backend

        private_key = serialization.load_pem_private_key(
            creds["private_key"].encode(), password=None, backend=default_backend()
        )
        signature = private_key.sign(signing_input, padding.PKCS1v15(), hashes.SHA256())
    except Exception as e:
        print(f"ERROR: Could not sign JWT: {e}")
        sys.exit(1)

    jwt = signing_input + b"." + b64(signature)

    token_url = "https://oauth2.googleapis.com/token"
    data = urllib.parse.urlencode({
        "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
        "assertion": jwt.decode(),
    }).encode()

    req = urllib.request.Request(token_url, data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())["access_token"]
    except urllib.error.HTTPError as e:
        print(f"ERROR: Token exchange failed: {e.code} {e.reason}")
        print(e.read().decode())
        sys.exit(1)


def query_gsc(access_token, start_date, end_date):
    """Fetch page-level GSC performance data."""
    url = f"https://searchconsole.googleapis.com/webmasters/v3/sites/{urllib.parse.quote(SITE_URL)}/searchAnalytics/query"
    body = json.dumps({
        "startDate": start_date,
        "endDate": end_date,
        "dimensions": ["page"],
        "rowLimit": 500,
    }).encode()

    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read()).get("rows", [])
    except urllib.error.HTTPError as e:
        print(f"ERROR: GSC query failed: {e.code} {e.reason}")
        print(e.read().decode())
        sys.exit(1)


def main():
    creds_json = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_JSON")
    if not creds_json:
        print("ERROR: GOOGLE_APPLICATION_CREDENTIALS_JSON env var not set")
        sys.exit(1)

    print("Getting access token...")
    token = get_access_token(creds_json)
    print("  Token obtained.")

    end_date = datetime.date.today() - datetime.timedelta(days=3)
    start_date = end_date - datetime.timedelta(days=LOOKBACK_DAYS)

    print(f"Querying GSC for {start_date} to {end_date}...")
    rows = query_gsc(token, start_date.isoformat(), end_date.isoformat())
    print(f"Got {len(rows)} pages with data.")

        SKIP_PATTERNS = ("/terms", "/privacy", "/contact", "/about", "/press", "/disclaimer", "/refund")

    striking = []
    for row in rows:
        pos = row.get("position", 0)
        url = row["keys"][0]
        if any(skip in url for skip in SKIP_PATTERNS):
            continue
        if STRIKING_MIN <= pos <= STRIKING_MAX:
            striking.append({
                "url": row["keys"][0],
                "position": pos,
                "impressions": int(row.get("impressions", 0)),
                "clicks": int(row.get("clicks", 0)),
                "ctr": row.get("ctr", 0),
            })

    striking.sort(key=lambda x: -x["impressions"])

    lines = [f"# Striking Distance Report\n"]
    lines.append(f"**Generated:** {datetime.date.today()}\n")
    lines.append(f"**Period:** {start_date} to {end_date} ({LOOKBACK_DAYS} days)\n")
    lines.append(f"**Pages in positions {STRIKING_MIN}-{STRIKING_MAX}:** {len(striking)}\n")

    if not striking:
        lines.append("\nNo pages currently in the striking distance range.")
        lines.append("\n**This is normal** for the first 2-4 weeks after submission.")
        lines.append("Google needs time to index and rank pages before GSC data appears.")
        lines.append("\nRe-run this workflow in 7 days to see initial data.")
    else:
        lines.append("\nPriority order (highest impressions first):\n")
        lines.append("| URL | Position | Impressions | Clicks | Action |")
        lines.append("|---|---|---|---|---|")
        for s in striking[:30]:
            if s["impressions"] > 200:
                action = "Add internal link from top page"
            elif s["impressions"] > 50:
                action = "Expand content + add FAQ"
            else:
                action = "Low priority"
            url_short = s["url"].replace("https://calccover.com/", "/")
            lines.append(f"| {url_short} | {s['position']:.1f} | {s['impressions']} | {s['clicks']} | {action} |")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"\nWrote {len(striking)} striking distance pages to {OUTPUT_FILE}")
    for s in striking[:5]:
        print(f"  pos {s['position']:.1f} | {s['impressions']:>5} impr | {s['url']}")


if __name__ == "__main__":
    main()
