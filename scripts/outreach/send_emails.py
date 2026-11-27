import csv, smtplib, os, datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = os.environ["SMTP_USER"]
SMTP_PASS = os.environ["SMTP_PASS"]
TRACKING_BASE_URL = os.environ.get("TRACKING_BASE_URL", "")

# Read targets
targets = []
with open("scripts/outreach/data/targets.csv", "r") as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row.get("Status", "").strip().lower() == "not sent":
            targets.append(row)

# Send emails
for t in targets:
    email = t["Contact Email"]
    if not email or email == "contact form":
        continue

    # Add tracking pixel
    track_id = t["#"]
    pixel = f'<img src="{TRACKING_BASE_URL}/pixel?id={track_id}" width="1" height="1" style="display:none;">' if TRACKING_BASE_URL else ""
    
    html = f"""
    <p>Hi {t.get('Contact Name', 'there')},</p>
    <p>I saw your piece on {t.get('Target URL', 'insurance')}...</p>
    <p>We just published a 2026 Commercial Property Insurance Rate Index. [Stats]</p>
    <p><a href="https://calccover.com/commercial-property-insurance-rate-index/">View the data</a></p>
    {pixel}
    """
    
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"2026 Commercial Property Rate Index (Data for {t['Target Site']})"
    msg["From"] = SMTP_USER
    msg["To"] = email
    
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, email, msg.as_string())
        print(f"Sent to {email}")
        
        # Update status
        t["Status"] = "Sent"
        t["Date Sent"] = datetime.date.today().isoformat()
    except Exception as e:
        print(f"Failed to send to {email}: {e}")
        t["Status"] = "Error"

# Write back to CSV
with open("scripts/outreach/data/targets.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=targets[0].keys())
    writer.writeheader()
    writer.writerows(targets)