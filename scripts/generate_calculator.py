#!/usr/bin/env python3
"""
Calccover — Automated Insurance Calculator Generator
Generates one new insurance calculator page per run using Gemini API.
"""
import os
import json
import re
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime

API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    print("ERROR: GEMINI_API_KEY environment variable is not set")
    sys.exit(1)

MODEL_CANDIDATES = [
    "gemini-3.5-flash",
    "gemini-3.8-flash",
    "gemini-2.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-2.5-flash-lite",
]

BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
QUEUE_FILE = "scripts/queue.json"
TIMEOUT_PER_ATTEMPT = 60
MAX_RETRIES_PER_MODEL = 2


def load_queue():
    with open(QUEUE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def pick_next(queue):
    for i, item in enumerate(queue):
        if item.get("status") != "done":
            return i, item
    return None, None


def save_queue(queue):
    with open(QUEUE_FILE, "w", encoding="utf-8") as f:
        json.dump(queue, f, indent=2)


def build_prompt(item):
    return f"""You are an expert web developer and commercial insurance industry writer.

Generate a complete single-file HTML page for an insurance calculator with these specs:

- Calculator name: {item['name']}
- Slug: {item['slug']}
- Purpose: {item['description']}
- Inputs: {item['inputs']}
- Formula/logic: {item['formula']}

REQUIREMENTS:
1. Output ONLY the full HTML file, starting with <!DOCTYPE html> and ending with </html>. No markdown fences, no explanation.
2. Use this exact CSS design system (LIGHT theme with blue accent). Every rule below must appear exactly:
   - `*{{margin:0;padding:0;box-sizing:border-box}}`
   - `body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;line-height:1.6;color:#1a1a1a;background:#fafafa}}`
   - `header{{background:#fff;border-bottom:1px solid #e5e5e5;padding:1rem 1.5rem}}`
   - `.container{{max-width:720px;margin:0 auto;padding:0 1.5rem}}`
   - `header .container{{display:flex;align-items:center;justify-content:space-between;max-width:960px}}`
   - `.logo{{font-size:1.4rem;font-weight:700;color:#0066cc;text-decoration:none}}`
   - `nav a{{margin-left:1.5rem;color:#555;text-decoration:none;font-size:.95rem}}`
   - `.calculator-box{{background:#fff;border:1px solid #e5e5e5;border-radius:8px;padding:1.5rem;margin:2rem 0}}`
   - `.form-group{{margin-bottom:1.25rem}}`
   - `label{{display:block;font-weight:500;margin-bottom:.4rem;font-size:.95rem}}`
   - `input,select{{width:100%;padding:.75rem;border:1px solid #ccc;border-radius:6px;font-size:1rem;font-family:inherit}}`
   - `button{{background:#0066cc;color:#fff;border:none;padding:1rem 2rem;font-size:1.05rem;font-weight:600;border-radius:6px;cursor:pointer;width:100%;margin-top:.5rem}}`
   - `button:hover{{background:#0052a3}}`
   - `.result-box{{background:#e6f0fa;border:2px solid #0066cc;border-radius:8px;padding:1.5rem;margin-top:1.5rem;text-align:center;display:none}}`
   - `.result-box.show{{display:block}}`
   - `.result-box .premium{{font-size:2rem;font-weight:700;color:#0066cc}}`
   - `.lead-form{{margin-top:1.5rem;display:none}}`
   - `.lead-form.show{{display:block}}`
   - `.lead-form button{{background:#28a745}}`
   - `.content-section{{background:#fff;border:1px solid #e5e5e5;border-radius:8px;padding:1.5rem;margin-bottom:2rem}}`
   - `footer{{border-top:1px solid #e5e5e5;padding:2rem 0;margin-top:3rem;color:#777;font-size:.9rem;background:#fff}}`
   Do NOT use CSS custom properties. Do NOT use dark theme. The primary action button MUST be #0066cc blue.
3. Header: `<header><div class="container"><a href="/" class="logo">Calccover</a><nav><a href="/about/">About</a><a href="/contact/">Contact</a></nav></div></header>`
4. Include a `.calculator-box` with labeled inputs relevant to commercial insurance (industry type, annual revenue, number of employees, state, coverage limits, claims history where applicable). All monetary values are in USD. No unit toggle is needed — insurance is a financial product, not a physical one. STRICT RULES — do not violate:
- Do NOT include internal calculation factors, base rates, multipliers, or any numeric annotation in the visible label or option text. For example, write "Retail" not "Retail (3,200 base)". Write "California" not "California (1.35X)".
- Do NOT prefill any input field. No value="..." attribute on number, text, or email inputs.
- Do NOT use the selected attribute on any <option>.
- All option text must be plain English names only.
- Factors and multipliers belong ONLY inside the JavaScript function, never in the HTML labels.
5. Include a `.result-box` (hidden by default, shows on Calculate) with result rows. Each row uses `<div class="result-row"><span class="label">...</span><span class="value">...</span></div>` inside the result box. Add CSS: `.result-row{{display:flex;justify-content:space-between;padding:.6rem 0;border-bottom:1px solid #c9dcf0}}` and `.result-row .label{{color:#555}}` and `.result-row .value{{color:#0066cc;font-weight:700}}`.
6. Include a `.lead-form` below the result box that appears when results show. Use this exact form structure:
<form action="https://api.web3forms.com/submit" method="POST">
    <input type="hidden" name="access_key" value="7ddf27ee-45e4-4fe4-afd3-5b802ece6846">
    <input type="email" name="email" required placeholder="your@email.com">
    <input type="hidden" name="calculator" value="{item['name']}">
    <input type="hidden" name="page_url" id="pageUrl" value="">
    <input type="hidden" name="subject" value="New quote request — {item['name']}">
    <input type="hidden" name="redirect" value="https://calccover.com/thank-you/">
    <button type="submit">Get a Free Quote</button>
</form>
<script>document.getElementById('pageUrl').value = window.location.href;</script>
No JavaScript alert functions. No FormSubmit. Form submits directly to Web3Forms.
The {item['name']} will be replaced with each calculator's actual name during generation. No JavaScript alert functions.
7. Include a collapsible `<details>` section immediately below the calculator (before content sections) titled "How this calculator works". Inside: 2-3 sentences explaining the formula in plain English, plus one line: "Formula source: [Source]." This <details> section is MANDATORY. Do not skip it. It must appear immediately after the lead form, before the first content H2.
8. Include 3 content sections, each wrapped in `<section class="content-section">`: "How Much Does [X] Cost?", "What Factors Affect Your Premium?", and "Frequently Asked Questions" with 3 Q&As each. Each section 100-200 words with real commercial insurance industry detail. Every content section MUST be wrapped in <section class="content-section">. The CSS MUST include .content-section{{background:#fff;border:1px solid #e5e5e5;border-radius:8px;padding:1.5rem;margin-bottom:2rem}}. Do NOT skip this wrapper.
9. For FAQ, use `<h3>Question</h3><p>Answer</p>` for each Q&A. Never put multiple Q&As in one `<p>`. Never use "Q:" or "A:" prefixes.
10. Include footer: `<footer><div class="container"><div><a href="/about/">About</a><a href="/contact/">Contact</a><a href="/privacy/">Privacy</a><a href="/terms/">Terms</a></div><div>© 2026 Calccover.</div></div></footer>`
11. Include JSON-LD schema: {{"@context":"https://schema.org","@type":"WebApplication","name":"{item['name']}","applicationCategory":"FinanceApplication","operatingSystem":"Web","offers":{{"@type":"Offer","price":"0","priceCurrency":"USD"}}}}
12. Include these two lines in the head exactly:
<script async src="https://www.googletagmanager.com/gtag/js?id=G-3KC8D1S3M2"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','G-3KC8D1S3M2');</script>
13. Include AdSense in the head:
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-2475849248056642" crossorigin="anonymous"></script>
14. Include in the head:
<link rel="canonical" href="https://calccover.com/{item['slug']}/">
<title>{item['name']} — Calccover</title>
<meta name="description" content="{item['description']}">
15. All JavaScript inline at bottom of body. Vanilla JS only. No external libraries.
16. Mobile responsive.
17. The calculator must produce correct estimates using the formula: {item['formula']}

Output the full HTML file now:"""


def call_gemini_once(prompt, model):
    url = BASE_URL.format(model=model, key=API_KEY)
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.4, "maxOutputTokens": 32768},
    }
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=TIMEOUT_PER_ATTEMPT) as resp:
        return json.loads(resp.read().decode("utf-8"))


def call_gemini_with_retries(prompt, model):
    last_error = None
    for attempt in range(MAX_RETRIES_PER_MODEL):
        try:
            print(f"  Attempt {attempt + 1}/{MAX_RETRIES_PER_MODEL} with {model}")
            data = call_gemini_once(prompt, model)
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8", errors="replace")
            print(f"  HTTP {e.code}: {error_body[:200]}")
            last_error = e
            if e.code in (429, 500, 502, 503, 504):
                time.sleep(5 * (attempt + 1))
                continue
            raise
        except (TimeoutError, urllib.error.URLError) as e:
            print(f"  Network error: {e}")
            last_error = e
            time.sleep(5 * (attempt + 1))
            continue
    raise RuntimeError(f"All attempts failed for {model}: {last_error}")


def generate_with_fallback(prompt):
    errors = []
    for model in MODEL_CANDIDATES:
        print(f"Trying model: {model}")
        try:
            result = call_gemini_with_retries(prompt, model)
            print(f"Success with model: {model}")
            return result
        except Exception as e:
            errors.append(f"{model}: {e}")
            continue
    raise RuntimeError("All models failed:\n" + "\n".join(errors))


def extract_html(text):
    text = text.strip()
    text = re.sub(r"^```html\s*", "", text)
    text = re.sub(r"^```\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    start = text.find("<!DOCTYPE html>")
    if start == -1:
        start = text.find("<html")
    end = text.rfind("</html>")
    if start != -1 and end != -1:
        return text[start:end + len("</html>")]
    if start != -1:
        print("WARNING: Truncated response, closing tags")
        truncated = text[start:]
        if "<body" in truncated:
            if "</body>" not in truncated:
                truncated += "\n</body>"
            if "</html>" not in truncated:
                truncated += "\n</html>"
            return truncated
    raise ValueError("Could not extract HTML")


def write_page(slug, html):
    os.makedirs(slug, exist_ok=True)
    path = os.path.join(slug, "index.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Wrote {path} ({len(html)} bytes)")


def update_sitemap(slug):
    path = "sitemap.xml"
    with open(path, "r", encoding="utf-8") as f:
        sitemap = f.read()
    url = f"https://calccover.com/{slug}/"
    if url in sitemap:
        return
    entry = f'<url><loc>{url}</loc><priority>0.9</priority></url>\n'
    sitemap = sitemap.replace("</urlset>", entry + "</urlset>")
    with open(path, "w", encoding="utf-8") as f:
        f.write(sitemap)
    print(f"Added {url} to sitemap")


def update_homepage(slug, name, description):
    path = "index.html"
    with open(path, "r", encoding="utf-8") as f:
        home = f.read()
    if f'href="/{slug}/"' in home:
        print("Already on homepage")
        return
    card = f'<a href="/{slug}/" class="card"><h3>{name}</h3><p>{description}</p></a>\n'
    marker = '<div class="grid">'
    last_grid = home.rfind(marker)
    if last_grid == -1:
        print("Could not find grid")
        return
    close_idx = home.find("</div>", last_grid)
    if close_idx == -1:
        return
    home = home[:close_idx] + card + home[close_idx:]
    with open(path, "w", encoding="utf-8") as f:
        f.write(home)
    print(f"Added {name} to homepage")


def main():
    queue = load_queue()
    idx, item = pick_next(queue)
    if item is None:
        print("Queue empty")
        return
    print(f"Generating: {item['name']} ({item['slug']})")
    prompt = build_prompt(item)
    raw = generate_with_fallback(prompt)
    html = extract_html(raw)
    write_page(item["slug"], html)
    update_sitemap(item["slug"])
    update_homepage(item["slug"], item["name"], item["description"])
    queue[idx]["status"] = "done"
    queue[idx]["generated_at"] = datetime.utcnow().isoformat() + "Z"
    save_queue(queue)
    print("Done.")


if __name__ == "__main__":
    main()
