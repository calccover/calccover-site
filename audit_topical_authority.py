import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from collections import defaultdict
import xml.etree.ElementTree as ET
import time

# --- CONFIGURATION ---
SITEMAP_URL = "https://calccover.com/sitemap.xml"
# Crawl a sample for speed. Set to None to check all 137 URLs (slower).
MAX_URLS_TO_CHECK = 137
# --- ---

def get_urls_from_sitemap(sitemap_url):
    """Fetches and parses all URLs from the sitemap."""
    try:
        response = requests.get(sitemap_url, timeout=10)
        response.raise_for_status()
        root = ET.fromstring(response.content)
        # Find all <loc> tags regardless of namespace
        urls = [element.text for element in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc')]
        return urls
    except Exception as e:
        print(f"Error fetching sitemap: {e}")
        return []

def analyze_internal_links(urls):
    """Crawls each URL and maps all internal links found on the page."""
    link_graph = defaultdict(list)  # target_url -> list of source_urls
    base_domain = urlparse(urls[0]).netloc
    
    with requests.Session() as session:
        session.headers.update({'User-Agent': 'Calccover-Authority-Audit/1.0'})
        
        for i, source_url in enumerate(urls):
            print(f"[{i+1}/{len(urls)}] Crawling {source_url}")
            try:
                # Use GET to ensure content is retrieved; check content type to avoid parsing non-HTML
                response = session.get(source_url, timeout=10)
                if 'text/html' not in response.headers.get('Content-Type', ''):
                    continue
                    
                soup = BeautifulSoup(response.content, 'html.parser')
                
                for a_tag in soup.find_all('a', href=True):
                    absolute_target = urljoin(source_url, a_tag['href'])
                    parsed_target = urlparse(absolute_target)
                    
                    # Ensure the link is internal and is a normal web page
                    if parsed_target.netloc == base_domain and parsed_target.scheme in ['http', 'https']:
                        normalized_target = absolute_target.rstrip('/')
                        if source_url.rstrip('/') != normalized_target:
                            link_graph[normalized_target].append(source_url)
                            
                time.sleep(0.3) # Be polite to the server
                
            except Exception as e:
                print(f"  -> Error processing {source_url}: {e}")

    return link_graph

def generate_report(urls, link_graph):
    """Analyzes the link graph and prints a structured report."""
    print("\n" + "="*60)
    print("TOPICAL AUTHORITY & INTERNAL LINK AUDIT REPORT")
    print("="*60)

    # --- A. Authority Hubs (Pages with the most outbound internal links) ---
    source_counts = defaultdict(int)
    for target, sources in link_graph.items():
        for source in sources:
            source_counts[source] += 1
            
    top_hubs = sorted(source_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    
    print("\n--- 📈 TOP 10 AUTHORITY HUBS (Most Outbound Internal Links) ---")
    print("These are your strongest pages for passing link equity. They should link to target pages.")
    for url, count in top_hubs:
        print(f"  - [{count} links] {url}")

    # --- B. Orphan Pages (No inbound internal links found) ---
    all_sitemap_urls_normalized = {u.rstrip('/') for u in urls}
    orphan_pages = [url for url in urls if url.rstrip('/') not in link_graph]
    
    print("\n--- ⚠️ POTENTIAL ORPHAN PAGES (No Inbound Internal Links Found) ---")
    if orphan_pages:
        for page in orphan_pages[:20]: # Show first 20
            print(f"  - {page}")
    else:
        print("  - None found. All pages have at least one inbound internal link.")

    # --- C. Target Analysis: Commercial Property Cluster ---
    target_calc = "https://calccover.com/commercial-property-insurance-calculator"
    target_cost = "https://calccover.com/commercial-property-insurance-cost"
    
    print(f"\n--- 🎯 TARGET ANALYSIS: Commercial Property Cluster ---")
    
    for name, url in [("Calculator", target_calc), ("Cost Guide", target_cost)]:
        inbound = link_graph.get(url, [])
        print(f"\n  [>] {name}: {url}")
        print(f"      Found {len(inbound)} inbound internal links.")
        if inbound:
            print(f"      Top 5 sources: {', '.join(inbound[:5])}")

    # --- D. Cluster Link Verification (Bidirectional linking) ---
    calc_to_cost = target_cost in link_graph.get(target_calc, [])
    cost_to_calc = target_calc in link_graph.get(target_cost, [])
    
    print(f"\n--- 🔗 BIDIRECTIONAL LINK CHECK (Cluster Integrity) ---")
    print(f"  - Calculator -> Cost Guide: {'✅ YES' if calc_to_cost else '❌ NO'}")
    print(f"  - Cost Guide -> Calculator: {'✅ YES' if cost_to_calc else '❌ NO'}")
    if calc_to_cost and cost_to_calc:
        print("  -> The core cluster is closed. Link equity flows both ways.")
    else:
        print("  -> The cluster has a gap. Add the missing link to strengthen topical authority.")

if __name__ == "__main__":
    print("Fetching sitemap...")
    all_site_urls = get_urls_from_sitemap(SITEMAP_URL)
    
    if all_site_urls:
        urls_to_crawl = all_site_urls[:MAX_URLS_TO_CHECK]
        print(f"Found {len(all_site_urls)} URLs. Starting crawl of {len(urls_to_crawl)} pages...")
        internal_link_graph = analyze_internal_links(urls_to_crawl)
        generate_report(urls_to_crawl, internal_link_graph)
    else:
        print("Could not retrieve sitemap. Audit aborted.")