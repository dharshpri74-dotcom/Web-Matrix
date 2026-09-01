"""
FinVerse — Synthetic SEBI Filing / Earnings Transcript Generator
Generates 15-20 realistic synthetic filing text files for RAG demo.
"""
import os
import random

CORPUS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "corpus")

FILINGS = [
    {
        "id": "SEBI-RELIANCE-2025-Q4",
        "title": "Reliance Industries Ltd — Q4 FY2025 Earnings Call Transcript",
        "content": """RELIANCE INDUSTRIES LIMITED
Q4 FY2025 Earnings Call — May 2025

Chairman Mukesh Ambani: "Reliance delivered robust performance across all three verticals this quarter. Jio crossed 500 million subscribers, and our ARPU improved to ₹192, reflecting strong data consumption trends. Retail revenue grew 18% YoY, driven by expansion into Tier-2 and Tier-3 cities. Our new energy business is on track with the Jamnagar gigafactory construction progressing ahead of schedule.

EBITDA for the quarter stood at ₹62,100 crore, up 12% YoY. Net profit was ₹19,400 crore. The petrochemical business faced margin pressure due to elevated crude oil prices, but we expect normalization in H2.

Capital expenditure guidance remains at ₹1.2 lakh crore for FY2026, primarily directed towards 5G network expansion, retail store rollout, and green energy initiatives.

Our debt-to-equity ratio stands at 0.42, well within comfortable levels. Free cash flow generation remains strong at ₹52,000 crore annually."""
    },
    {
        "id": "SEBI-TCS-2025-Q4",
        "title": "TCS — Q4 FY2025 Results & Management Commentary",
        "content": """TATA CONSULTANCY SERVICES LIMITED
Q4 FY2025 Results — April 2025

CEO K. Krithivasan: "TCS posted industry-leading growth in Q4, with revenue growing 14.2% in constant currency terms. Our deal pipeline remains robust with TCV of $12.2 billion in Q4 alone. BFSI vertical grew 16%, and we saw strong demand from European banks for core banking modernization.

Attrition has stabilized at 11.8%, and we added 28,000 associates net this quarter. Our AI and GenAI practice now spans 450+ client engagements. We invested ₹1,800 crore in upskilling our workforce on AI capabilities.

EBIT margin expanded to 27.8% from 25.3% a year ago, reflecting improved project mix and automation-driven productivity gains. We expect this margin trajectory to sustain.

We are seeing early signs of recovery in the discretionary spending environment, particularly in North American retail and European manufacturing."""
    },
    {
        "id": "SEBI-HDFCBANK-2025-Q4",
        "title": "HDFC Bank — Q4 FY2025 Investor Presentation",
        "content": """HDFC BANK LIMITED
Q4 FY2025 Investor Presentation

MD & CEO Sashidhar Jagdishan: "Post the merger integration, HDFC Bank has emerged stronger. Total deposits grew 15.6% YoY to ₹24.5 lakh crore. The merger synergies are ahead of schedule — we expect ₹5,000 crore annual cost savings by FY2027.

Net Interest Margin compressed slightly to 3.44% from 3.51% due to the deposit repricing environment, but we see stabilization ahead. Asset quality remains pristine with GNPA at 1.24% and NNPA at 0.33%.

Our digital platform onboarded 4.2 million new customers in Q4. We processed 5.8 billion UPI transactions, maintaining our leadership position. The credit card portfolio crossed 2 crore cards.

We recommend a final dividend of ₹22 per share. Our CET1 ratio at 19.2% provides ample headroom for growth."""
    },
    {
        "id": "SEBI-INFY-2025-Q4",
        "title": "Infosys — Q4 FY2025 Earnings & Guidance Update",
        "content": """INFOSYS LIMITED
Q4 FY2025 Results & Guidance

CEO Salil Parekh: "Infosys delivered another quarter of strong broad-based growth. Revenue in constant currency grew 11.8% YoY. Our large deal momentum continued with $8.1 billion TCV, including 5 mega deals.

The top 5 verticals all grew in double digits. Financial services recovered strongly with 13% growth. Our Cobalt cloud platform now has 45,000 assets, and 85% of our new deals include cloud and AI components.

We are raising our FY2026 revenue guidance to 12-14% growth in CC terms and operating margin guidance to 26-28%. Our PerfidAI platform for fraud detection has been adopted by 12 major banks.

Free cash flow conversion improved to 92% of net profit. We returned ₹32,000 crore to shareholders through dividends and buybacks in FY2025."""
    },
    {
        "id": "SEBI-SBIN-2025-Q4",
        "title": "State Bank of India — Q4 FY2025 Results",
        "content": """STATE BANK OF INDIA
Q4 FY2025 Results

Chairman Dinesh Kumar Khara: "SBI delivered its strongest ever quarterly performance. Net profit for Q4 was ₹21,200 crore, up 24% YoY. For the full year, PAT crossed ₹70,000 crore milestone.

Credit growth accelerated to 16.2%, driven by retail and MSME segments. Our NIM improved to 3.47% due to better asset-liability management. GNPA ratio improved to 2.15% from 2.78% a year ago, reflecting clean balance sheet.

YONO platform crossed 95 million registered users. Digital lending now accounts for 38% of total retail loan disbursements. We disbursed ₹2.1 lakh crore through digital channels.

Our NPA recovery through IBC and other channels recovered ₹18,500 crore this year. Provision coverage ratio stands at 75.2%."""
    },
    {
        "id": "SEBI-ITC-2025-Q4",
        "title": "ITC Limited — FY2025 Annual Report Excerpt",
        "content": """ITC LIMITED
FY2025 Annual Report — Business Segment Review

Chairman Sanjiv Puri: "ITC's multi-dimensional growth strategy continues to deliver. Our FMCG segment revenue grew 12% to ₹21,000 crore, with EBITDA margins expanding 200bps. The Hotels business posted its best-ever year with revenue of ₹9,200 crore and margins exceeding 40%.

Agriculture Business leveraged ITC's agri-infrastructure to achieve revenue of ₹22,000 crore. OurPaperboards & Specialty Products division benefited from import substitution trends.

ITC's sustainability initiatives have saved 4.5 million tonnes of CO2 equivalent annually. We are on track to be carbon positive for the 19th consecutive year. Water positive for 18 years.

We are investing ₹5,000 crore in our new FMCG categories — premium personal care and health foods. Our distribution network now covers 8 million retail outlets across India."""
    },
    {
        "id": "SEBI-TATAMOTORS-2025-Q4",
        "title": "Tata Motors — Q4 FY2025 Results & JLR Performance",
        "content": """TATA MOTORS LIMITED
Q4 FY2025 Results

Managing Director Günter Butschek: "Tata Motors reported consolidated revenue of ₹1.2 lakh crore in Q4, up 13% YoY. JLR maintained its strong performance with EBIT margin at 8.2%, driven by Range Rover and Defender demand.

Domestic PV business grew 22% with strong EV adoption — our EV market share crossed 62%. The Punch.ev and Nexon.ev continued their dominance. We sold 28,000 EVs in Q4 alone, a 45% YoY increase.

Commercial vehicles faced a cyclical downturn but we maintained market leadership at 38% share. We expect CV demand to recover in H2 with infrastructure spending.

Our net automotive debt reduced to ₹28,000 crore, on track for zero net debt by FY2027."""
    },
    {
        "id": "SEBI-WIPRO-2025-Q4",
        "title": "Wipro — Q4 FY2025 Quarterly Update",
        "content": """WIPRO LIMITED
Q4 FY2025 Results

CEO Srini Pallia: "Wipro delivered revenues of ₹23,200 crore in Q4, representing 10.5% YoY growth in constant currency. Our transformation strategy is bearing fruit — the top 10 client relationships grew 18%.

The BFSI vertical saw a strong recovery with 14% growth. Healthcare & life sciences emerged as a new growth engine with 22% growth. Our AI360 practice now has 1,000+ consultants and serves 200 clients.

Operating margins improved to 16.8% from 14.2% a year ago through operational improvements and portfolio optimization. We guided for 17-19% margins in FY2026.

Total contract value was $4.6 billion in Q4. We completed 3 strategic acquisitions to strengthen our cloud and data capabilities."""
    },
    {
        "id": "SEBI-LT-2025-Q4",
        "title": "Larsen & Toubro — Q4 FY2025 Order Book Update",
        "content": """LARSEN & TOUBRO LIMITED
Q4 FY2025 Results & Order Book Update

Whole-time Director & CEO S N Subrahmanyan: "L&T secured orders worth ₹78,000 crore in Q4, taking the full-year order intake to ₹2.5 lakh crore — a record. The consolidated order book stands at ₹4.8 lakh crore, providing strong revenue visibility.

Our E&C segment benefited from the government's infrastructure push. International orders contributed 38% of Q4 intake, reflecting growing export opportunity. The IT&TS segment grew 12% with robust demand for digital transformation services.

Revenue for FY2025 was ₹2.2 lakh crore with EBITDA margin at 12.5%. We are targeting 13%+ margins in FY2026 through better project execution and mix improvement.

Our renewable energy order book crossed ₹15,000 crore, positioning us well for the energy transition theme."""
    },
    {
        "id": "SEBI-BHARTIARTL-2025-Q4",
        "title": "Bharti Airtel — Q4 FY2025 Earnings",
        "content": """BHARTI AIRTEL LIMITED
Q4 FY2025 Results

MD & CEO Gopal Vittal: "Airtel delivered yet another quarter of strong execution. India revenue grew 12% YoY driven by both mobile and homes business. ARPU improved to ₹245, up 18% YoY, crossing the ₹200 mark sustainably.

5G coverage now extends to 8,000 cities. We added 4.5 million 5G subscribers in Q4. Enterprise business grew 15% with strong demand for cybersecurity and managed network services.

Africa business delivered constant currency revenue growth of 10%. Our digital TV business stabilized with 16.5 million subscribers.

Consolidated free cash flow was ₹18,500 crore for FY2025. Net debt to EBITDA improved to 2.5x. We expect ARPU to cross ₹300 over the next 18 months."""
    },
    {
        "id": "SEBI-ICICIBANK-2025-Q4",
        "title": "ICICI Bank — Q4 FY2025 Investor Call",
        "content": """ICICI BANK LIMITED
Q4 FY2025 Investor Call

MD & CEO Sandeep Bakhshi: "ICICI Bank reported PAT of ₹12,800 crore in Q4, up 18% YoY. Net Interest Income grew 14% and Other Income grew 22%, demonstrating diversified revenue growth.

Asset quality continued to improve — GNPA at 1.96% and NNPA at 0.42%. Provision coverage ratio at 77% provides adequate cushion. Retail loan portfolio grew 18%, with home loans and auto loans leading.

Our digital platform iMobile Pay crossed 35 million users. We processed ₹4.5 lakh crore in UPI transactions. The InstaBIZ platform for SMEs onboarded 200,000 new businesses.

CET1 ratio at 19.6% is well above regulatory requirements. We are well-capitalized for the next phase of growth."""
    },
    {
        "id": "SEBI-SUNPHARMA-2025-Q4",
        "title": "Sun Pharmaceutical — Q4 FY2025 Performance Review",
        "content": """SUN PHARMACEUTICAL INDUSTRIES LIMITED
Q4 FY2025 Performance Review

Managing Director Dilip Shanghvi: "Sun Pharma reported consolidated revenue of ₹12,600 crore in Q4, up 11% YoY. Specialty business in the US grew 25%, driven by Ilumya and Winlevi launches. US formulations now contribute 38% of total revenue.

Domestic formulations grew 8%, maintaining our leadership position with 8.5% market share. Chronic therapy segments — particularly cardiovascular, anti-diabetic, and oncology — outperformed.

EBITDA margin improved to 26.2% from 23.8%, driven by specialty product mix and operational efficiency. R&D spend was ₹850 crore, with focus on biosimilars and complex generics.

Our pipeline includes 15 ANDAs pending approval and 5 biosimilar filings. We are investing in gene therapy research through our Iran-based subsidiary."""
    },
    {
        "id": "SEBI-KOTAKBANK-2025-Q4",
        "title": "Kotak Mahindra Bank — Q4 FY2025 Update",
        "content": """KOTAK MAHINDRA BANK LIMITED
Q4 FY2025 Update

MD & CEO Ashok Vaswani: "Kotak Bank delivered a solid Q4 with net profit of ₹5,200 crore, up 16% YoY. Deposit growth at 14% was broad-based across segments. CASA ratio at 42% provides a strong low-cost funding base.

Credit growth was 15%, with retail loans growing 18%. Our housing loan book crossed ₹1 lakh crore milestone. The credit card portfolio grew 25% with 1.2 million new cards issued.

NIM at 4.32% remained among the highest in the industry. GNPA improved to 1.65% with strong collections and underwriting standards.

Our subsidiary Kotak Mahindra General Insurance grew 20%, and Kotak Securities saw a 30% increase in demat account additions."""
    },
    {
        "id": "SEBI-ADANIENT-2025-Q4",
        "title": "Adani Enterprises — Q4 FY2025 Results",
        "content": """ADANI ENTERPRISES LIMITED
Q4 FY2025 Results

Chairman Gautam Adani: "Adani Enterprises delivered consolidated revenue of ₹32,000 crore in Q4, up 35% YoY. Our portfolio companies across infrastructure, energy, and digital continue to scale rapidly.

New energy business secured PPAs worth ₹15,000 crore for 8 GW of solar and wind capacity. The AdaniConnex data center business added 100 MW capacity, now operating at 85% utilization.

Our airports business handled 28 million passengers in Q4, a 22% YoY increase. Mumbai airport expansion is on track for completion by Q2 FY2026.

Net debt to EBITDA improved to 3.8x. We remain committed to our deleveraging roadmap and expect to reduce this to below 3x by FY2027."""
    },
    {
        "id": "SEBI-NIFTY50-OUTLOOK-2025",
        "title": "Nifty 50 Index — FY2026 Market Outlook Report",
        "content": """NIFTY 50 INDEX — FY2026 OUTLOOK
Research Report — April 2025

Key themes for FY2026:
1. GDP growth expected at 6.8-7.2%, driven by government capex and rural consumption recovery.
2. RBI likely to maintain accommodative stance with 50-75bps rate cuts through the year.
3. Corporate earnings growth expected at 14-16% for Nifty50 companies.
4. FII flows likely to normalize as India's relative valuation becomes attractive vs China.
5. Manufacturing and PLI beneficiaries to outperform — focus on electronics, chemicals, and defense.
6. PSU stocks may continue their re-rating as government reforms deepen.
7. Banking sector NIMs may compress but credit growth will drive profitability.
8. IT sector recovery expected in H2 as discretionary spending improves globally.
9. EV transition accelerates — Tata Motors and M&M well positioned.
10. Green energy capex creates multi-year opportunities across the value chain.

Risks: Global recession, crude oil above $100, geopolitical escalation, and El Niño impact on monsoons.

Target Nifty50: 26,500 by December 2025 (base case), implying 15% upside from current levels."""
    },
]


def generate_all_filings():
    """Write all synthetic filings to the corpus directory."""
    os.makedirs(CORPUS_DIR, exist_ok=True)
    for filing in FILINGS:
        filename = f"{filing['id'].replace(' ', '_')}.txt"
        filepath = os.path.join(CORPUS_DIR, filename)
        if not os.path.exists(filepath):
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"DOCUMENT ID: {filing['id']}\n")
                f.write(f"TITLE: {filing['title']}\n")
                f.write("=" * 60 + "\n\n")
                f.write(filing["content"])
            print(f"  ✓ Generated: {filename}")
        else:
            print(f"  • Exists: {filename}")
    print(f"\n  Corpus: {len(FILINGS)} filings in {CORPUS_DIR}")


if __name__ == "__main__":
    generate_all_filings()
