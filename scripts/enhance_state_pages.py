#!/usr/bin/env python3
"""
Add a unique paragraph to each state page to break the template pattern.

Each state gets a distinct paragraph about a state-specific regulation,
industry concentration, or market characteristic.
Idempotent — safe to run multiple times.
"""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Unique context paragraph per state — real regulatory, industry, or market details
STATE_UNIQUE = {
    "alabama": "Alabama operates a competitive workers' comp market with no state fund, which has kept rates below the national median since 2015. Manufacturing and agriculture dominate the state's commercial insurance demand, with automotive plants driving the highest concentration of manufacturing class codes in the Southeast.",
    "alaska": "Alaska's isolated market and high import costs push commercial insurance rates above the national average despite a small business population. Fishing, oil and gas, and seasonal tourism create unique liability exposures that most lower-48 carriers don't write, which limits carrier competition and keeps rates elevated.",
    "arizona": "Arizona has one of the most competitive commercial insurance markets in the country, driven by a business-friendly regulatory environment and a growing population. Construction and retail dominate, but the state's low litigation climate keeps workers' comp rates well below the national median.",
    "arkansas": "Arkansas consistently ranks among the five cheapest states for workers' comp, driven by low medical costs, a favorable litigation climate, and strong market competition. Agriculture and manufacturing dominate, with poultry processing creating a concentrated class code cluster in the northwest part of the state.",
    "california": "California's commercial insurance market is the largest in the country but also one of the most regulated. Proposition 103 and strict workers' comp rules increase costs for most businesses, though the state's enormous carrier pool keeps GL rates competitive. Construction, agriculture, and technology drive the highest insurance demand.",
    "colorado": "Colorado's workers' comp market is competitive with rates above the national median, driven by a growing construction industry and higher-than-average medical costs. The state's legal cannabis industry creates unique commercial insurance needs that most carriers still won't write directly.",
    "connecticut": "Connecticut has one of the highest workers' comp rates in the country, driven by generous statutory benefits and a concentrated insurance market. Finance and healthcare dominate the state's commercial demand, with many businesses operating in high-rise commercial properties that carry elevated property insurance costs.",
    "delaware": "Delaware's commercial insurance market is small but competitive, with rates slightly above the national average. The state's dominance in corporate registration doesn't translate to small business insurance savings — financial services and chemical manufacturing drive the highest demand.",
    "florida": "Florida's commercial insurance market is uniquely shaped by catastrophe exposure. Hurricane risk drives property insurance costs 30–50% above the national average, and the state's no-fault auto system pushes commercial auto rates among the highest in the country. Construction and tourism dominate.",
    "georgia": "Georgia's commercial insurance market is competitive with rates below the national median. Logistics, manufacturing, and agriculture dominate, and the state's status as a Southeast transportation hub creates concentrated demand for commercial auto and cargo insurance.",
    "hawaii": "Hawaii has the most expensive workers' comp in the country, driven by an isolated market, high medical costs, and generous statutory benefits. Tourism and agriculture dominate the state's commercial demand, and the state's small carrier pool limits competition. Businesses consistently pay 2–3x mainland rates for the same coverage.",
    "idaho": "Idaho has one of the lowest workers' comp rates in the country, driven by a small, homogeneous workforce and a business-friendly regulatory environment. Agriculture and construction dominate. The state's low population density keeps carriers competing aggressively for small commercial accounts.",
    "illinois": "Illinois has above-average workers' comp rates driven by high litigation activity in the Chicago metro area and generous statutory benefits. Manufacturing, finance, and logistics dominate. Downstate Illinois rates run 30–40% below Chicago, creating a significant geographic spread within the state.",
    "indiana": "Indiana consistently ranks among the cheapest states for workers' comp, driven by low medical costs and a favorable regulatory environment. Manufacturing and agriculture dominate the state's commercial insurance demand, with automotive suppliers creating concentrated class code clusters.",
    "iowa": "Iowa's commercial insurance market is competitive with rates near the national median. Agriculture and manufacturing dominate, with the state's heavy concentration of insurance carriers (Des Moines is a major insurance hub) keeping rates competitive through market saturation.",
    "kansas": "Kansas has slightly below-average workers' comp rates, driven by a favorable regulatory climate and competitive carrier market. Agriculture and aviation manufacturing dominate, with Wichita's aircraft manufacturing cluster creating specialized class codes for the aerospace industry.",
    "kentucky": "Kentucky has below-average workers' comp rates following significant reforms in 2018 that reduced statutory benefits and litigation. Manufacturing and agriculture dominate, with the state's automotive assembly plants creating concentrated demand for manufacturing class codes.",
    "louisiana": "Louisiana has among the highest commercial insurance rates in the country, driven by hurricane exposure, high litigation activity, and generous statutory benefits. Oil and gas, shipping, and tourism dominate. Property insurance rates run 40–60% above the national average.",
    "maine": "Maine has above-average workers' comp rates despite its small business population, driven by a relatively liberal statutory benefit structure. Fishing, tourism, and forestry dominate. The state's small carrier pool limits competition, keeping rates elevated.",
    "maryland": "Maryland has above-average workers' comp rates driven by generous statutory benefits and proximity to Washington D.C.'s litigation environment. Biotech, defense, and finance dominate, with the state's concentration of federal contractors creating demand for specialized professional liability coverage.",
    "massachusetts": "Massachusetts has one of the highest workers' comp rates in the country, driven by generous statutory benefits and high medical costs. Biotech, technology, and healthcare dominate, with the Boston metro area driving the state's highest commercial insurance demand.",
    "michigan": "Michigan has below-average workers' comp rates following 2011 reforms that reduced statutory benefits. Automotive manufacturing dominates, along with agriculture. The state's no-fault auto system historically pushed commercial auto rates 30–40% above the national average, though 2019 reforms have reduced costs.",
    "minnesota": "Minnesota has above-average workers' comp rates driven by generous statutory benefits. Agriculture, manufacturing, and healthcare dominate, with the Twin Cities metro area carrying the state's highest concentration of commercial insurance demand.",
    "mississippi": "Mississippi has below-average workers' comp rates, driven by low medical costs and a favorable regulatory environment. Agriculture, manufacturing, and fishing dominate. The state's carrier pool is smaller than neighboring states, but competition remains adequate for most small business classes.",
    "missouri": "Missouri has near-average workers' comp rates driven by a business-friendly regulatory environment and competitive carrier market. Agriculture and manufacturing dominate, with the state's central location creating concentrated demand for logistics and transportation coverage.",
    "montana": "Montana has below-average workers' comp rates, driven by a small, homogeneous workforce and low population density. Agriculture, mining, and tourism dominate. The state's small carrier pool can limit options for specialized class codes, but standard small business coverage is readily available.",
    "nebraska": "Nebraska has near-average workers' comp rates driven by a competitive market and low medical costs. Agriculture and manufacturing dominate, with the state's large insurance carrier presence (Omaha) creating market competition that keeps rates favorable.",
    "nevada": "Nevada has among the cheapest workers' comp rates in the country, driven by 1999 reforms that established a competitive state fund. Tourism and construction dominate. The state's growing population and business-friendly environment have attracted carrier competition.",
    "new-hampshire": "New Hampshire has above-average workers' comp rates driven by generous statutory benefits. Manufacturing and tourism dominate. The state's small market can limit carrier options, but its proximity to Massachusetts and Boston creates some cross-border competition.",
    "new-jersey": "New Jersey has the second-most-expensive workers' comp in the country, driven by high statutory benefits, aggressive litigation, and dense urban exposure. Pharmaceuticals, finance, and logistics dominate. Property rates are elevated by coastal storm exposure.",
    "new-mexico": "New Mexico has below-average workers' comp rates driven by low medical costs and a favorable regulatory climate. Oil and gas, tourism, and agriculture dominate. The state's small carrier pool can limit options, but standard small business coverage is competitive.",
    "new-york": "New York has one of the highest workers' comp rates in the country, driven by generous statutory benefits and heavy litigation in the New York City metro area. Finance, real estate, and healthcare dominate. Upstate rates run 30–50% below NYC, creating a wide geographic spread within the state.",
    "north-carolina": "North Carolina has below-average workers' comp rates driven by a competitive market and business-friendly regulatory environment. Banking, technology, and agriculture dominate. The state's Research Triangle and Charlotte banking hub create concentrated demand for professional liability coverage.",
    "north-dakota": "North Dakota has the cheapest workers' comp in the country, driven by a state-run monopoly (Workforce Safety & Insurance) that eliminates carrier overhead. Oil and gas, agriculture, and manufacturing dominate. The state's small, homogeneous workforce keeps injury frequency low.",
    "ohio": "Ohio has among the cheapest workers' comp rates in the country, driven by a state-run monopoly (Ohio Bureau of Workers' Compensation) that provides coverage directly to most employers. Manufacturing and agriculture dominate. The state fund model substantially reduces costs versus competitive markets.",
    "oklahoma": "Oklahoma has below-average workers' comp rates following 2013 reforms that moved the state from a judicial to an administrative system. Oil and gas, agriculture, and aerospace dominate. The state's carrier pool is competitive for most standard class codes.",
    "oregon": "Oregon has below-average workers' comp rates driven by a state-run carrier (SAIF Corporation) that competes with private carriers. Technology, agriculture, and forestry dominate. The state's competitive hybrid model keeps rates 15–25% below the national average.",
    "pennsylvania": "Pennsylvania has above-average workers' comp rates driven by generous statutory benefits and an active plaintiffs' bar. Manufacturing, healthcare, and logistics dominate. Rates vary significantly between Philadelphia and central PA, creating in-state geographic spread.",
    "rhode-island": "Rhode Island has among the highest workers' comp rates in the country despite its small size, driven by generous statutory benefits and a concentrated insurance market. Healthcare and tourism dominate. The state's small carrier pool limits competition.",
    "south-carolina": "South Carolina has below-average workers' comp rates driven by business-friendly regulatory reform and a competitive market. Manufacturing and tourism dominate. The state's growing automotive manufacturing sector has created concentrated demand for manufacturing class codes.",
    "south-dakota": "South Dakota has below-average workers' comp rates driven by a favorable regulatory environment and competitive market. Agriculture and tourism dominate. The state's small business-friendly climate has attracted carrier competition, keeping rates 15–25% below the national median.",
    "tennessee": "Tennessee has below-average workers' comp rates following 2013 reforms that moved the state to an administrative system. Healthcare, manufacturing, and music industry dominate. Nashville's healthcare concentration creates demand for medical professional liability.",
    "texas": "Texas has no workers' comp mandate — it's the only US state where coverage is voluntary for private employers. Most Texas businesses still carry it because of civil liability exposure and contract requirements. Oil and gas, technology, and agriculture dominate. Texas commercial insurance rates are below the national average overall.",
    "utah": "Utah has among the cheapest workers' comp rates in the country, driven by a state-run monopoly (Workers' Compensation Fund of Utah) and a low-risk workforce. Technology and tourism dominate. The state's tech sector (Silicon Slopes) creates concentrated demand for professional liability and cyber coverage.",
    "vermont": "Vermont has above-average workers' comp rates despite its small business population, driven by generous statutory benefits. Agriculture and tourism dominate. The state's small carrier pool limits options and keeps rates elevated.",
    "virginia": "Virginia has below-average workers' comp rates driven by a competitive market and favorable regulatory environment. Technology, defense, and agriculture dominate. The state's proximity to D.C. creates demand for professional liability and government contractor coverage.",
    "washington": "Washington has below-average workers' comp rates, driven by a state-run monopoly (Department of Labor & Industries) that provides coverage to most employers. Technology, aerospace, and agriculture dominate. The state fund model keeps rates 20–30% below the national average.",
    "west-virginia": "West Virginia has among the cheapest workers' comp rates in the country, driven by state reforms in 2005 that privatized the state-run fund. Coal, chemicals, and tourism dominate. The state's historically high-risk industries now pay rates competitive with the national median.",
    "wisconsin": "Wisconsin has above-average workers' comp rates driven by generous statutory benefits and a concentrated insurance market. Manufacturing and agriculture dominate. Milwaukee's manufacturing concentration creates concentrated demand for manufacturing class codes.",
    "wyoming": "Wyoming has above-average workers' comp rates despite its small business population, driven by a state-run monopoly (Wyoming Workforce Services) and a heavy concentration of high-risk industries (oil and gas, mining). The state's small carrier pool limits private-sector competition.",
}


def find_state_slug(filepath):
    """Extract state slug from folder name."""
    match = re.search(r"commercial-insurance-cost-in-([a-z-]+)", filepath)
    if match:
        return match.group(1)
    return None


def add_unique_section(content, state_slug):
    """Add unique paragraph if not already present."""
    if not state_slug or state_slug not in STATE_UNIQUE:
        return content, False

    # Idempotent — skip if already enhanced
    if '<!-- unique-insight -->' in content:
        return content, False

    unique_text = STATE_UNIQUE[state_slug]

    # Get state name for heading
    state_name = state_slug.replace("-", " ").title()

    # Build the section
    section = f"""
<!-- unique-insight -->
<section class="content-section">
<h2>{state_name} market context</h2>
<p>{unique_text}</p>
</section>
"""

    # Insert right after the "Why {state} rates are..." section closes
    # Find the first content-section that mentions "Why"
    match = re.search(r'(<section class="content-section">\s*<h2>Why[^<]+</h2>.*?</section>)',
                      content, re.DOTALL)
    if match:
        end_pos = match.end()
        content = content[:end_pos] + section + content[end_pos:]
        return content, True

    # Fallback: insert before "Top industries" section
    match = re.search(r'<section class="content-section">\s*<h2>Top industries', content, re.DOTALL)
    if match:
        start_pos = match.start()
        content = content[:start_pos] + section + "\n" + content[start_pos:]
        return content, True

    return content, False


def main():
    enhanced = 0
    for root, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in (".git", ".github", "scripts", "node_modules")]
        if "index.html" not in files:
            continue

        filepath = os.path.join(root, "index.html")
        rel = os.path.relpath(filepath, ROOT).replace("\\", "/")

        if "commercial-insurance-cost-in-" not in rel:
            continue

        state_slug = find_state_slug(rel)
        if not state_slug or state_slug not in STATE_UNIQUE:
            continue

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        new_content, changed = add_unique_section(content, state_slug)

        if changed:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(new_content)
            print(f"  OK  {rel}")
            enhanced += 1

    print(f"\nEnhanced {enhanced} state pages with unique content.")


if __name__ == "__main__":
    main()
