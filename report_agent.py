"""
report_agent.py — IncepifyAI Report & Routing Agent (Agent 8 of 8)
 
Assembles complete 16-section credit approval memo from all 7 prior agents.
Determines routing authority. Generates downloadable HTML memo.
Single Claude API call — no web search, no form, no external APIs.
"""
 
import anthropic
import json
import os
import re
from datetime import date
from pathlib import Path
from dotenv import load_dotenv
 
load_dotenv()
 
_PROMPT_PATH = Path("system_prompt_report.txt")
if not _PROMPT_PATH.exists():
    raise FileNotFoundError("system_prompt_report.txt not found.")
 
SYSTEM_PROMPT = _PROMPT_PATH.read_text()
MODEL         = "claude-sonnet-4-6"
client        = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
 
 
# ─────────────────────────────────────────────────────
# PUBLIC ENTRY POINTS
# ─────────────────────────────────────────────────────
 
def generate_report(all_agent_outputs: dict) -> dict:
    """
    Assemble the complete credit memo and routing decision.
    Args:
        all_agent_outputs: dict with keys:
            financial_result, collateral_result, kyc_stored,
            revenue_result, industry_result, management_result,
            risk_assessment_result
    Returns:
        dict: complete memo JSON with 16 sections + routing
    """
    return _run_claude_analysis(all_agent_outputs)
 
 
def get_all_mock_inputs() -> dict:
    """Mock inputs simulating all 7 prior agents for standalone testing."""
    return {
        "financial_result": {
            "credit_recommendation": {
                "overall_assessment": "SATISFACTORY",
                "primary_repayment_viability": "ADEQUATE",
                "narrative_summary": "Sunrise Manufacturing demonstrates satisfactory financial performance. DSCR of 1.38x base case provides adequate debt service coverage.",
            },
            "key_ratios": {
                "cashflow": {"dscr": 1.38},
                "leverage": {"debt_to_equity": 1.84, "interest_coverage": 3.2},
                "liquidity": {"current_ratio": 1.42},
            },
            "sensitivity_analysis": {
                "base_case": {"dscr_yr1": 1.38, "dscr_yr3": 1.21},
                "downside_case": {"dscr_yr1": 1.05, "revenue_stress_pct": -15},
            },
        },
        "collateral_result": {
            "coverage_summary": {
                "coverage_ratio_pct": 109.1,
                "coverage_status": "SHORTFALL",
                "minimum_required_pct": 150,
                "shortfall_or_surplus_000": -204500,
            },
            "pre_disbursement_conditions": [
                "Additional security of NGN 204.5m to bring coverage to 150%",
                "Governors Consent on warehouse property",
            ],
        },
        "kyc_stored": {
            "aggregate_assessment": {
                "overall_kyc_risk_rating": "HIGH",
                "due_diligence_tier": "EDD",
                "senior_management_approval_required": True,
            },
            "credit_memo_narrative": "HIGH KYC risk due to PEP-connected director. EDD completed.",
        },
        "revenue_result": {
            "relationship_score": {"tier": "SILVER", "score": 7},
            "revenue_analysis": {"roa_pct": 0.84, "yoy_growth_pct": 12.4},
            "credit_memo_narrative": "SILVER tier relationship with ROA of 0.84%. Revenue growing 12.4% YoY.",
        },
        "industry_result": {
            "industry_assessment": {
                "outlook": "STABLE",
                "industry_risk_rating": "MEDIUM",
                "credit_risk_implication": "NEUTRAL",
            },
            "industry_profile": {"sector": "Manufacturing — Food & Beverages"},
            "credit_memo_narrative": "MEDIUM industry risk. STABLE outlook. NEUTRAL credit implication.",
        },
        "management_result": {
            "management_assessment": {
                "overall_management_score": 7,
                "management_quality": "SATISFACTORY",
                "key_man_risk_identified": True,
                "key_man_description": "MD is primary operational decision-maker. No succession plan.",
            },
            "credit_memo_narrative": "SATISFACTORY management (7/10). Key man risk: MD.",
        },
        "risk_assessment_result": {
            "risk_summary": {
                "overall_credit_risk_rating": "WATCH",
                "credit_recommendation": "APPROVE WITH CONDITIONS",
                "recommendation_rationale": "Three resolvable conditions: collateral shortfall, PEP director, key man risk.",
            },
            "conditions_precedent": [
                "Additional security of NGN 204.5m pledged before first drawdown",
                "Key man life insurance — bank as beneficiary for full facility amount",
                "Senior management sign-off on EDD for PEP-connected director",
            ],
            "financial_covenants": [
                "DSCR >= 1.20x measured semi-annually",
                "Maximum leverage: Total Debt / EBITDA <= 3.5x",
                "Accounts domiciliation with the bank",
            ],
            "monitoring_requirements": [
                "Semi-annual financial statements within 60 days",
                "Annual collateral revaluation by CBN-approved valuer",
                "Director change notification within 5 business days",
            ],
            "credit_memo_narrative": "WATCH overall risk profile. APPROVE WITH CONDITIONS.",
        },
    }
 
 
def get_mock_report_result() -> dict:
    """Full static mock of Agent 8 output. Zero API calls."""
    today = str(date.today().strftime("%d %B %Y"))
    return {
        "memo_metadata": {
            "memo_reference":            f"CAG/{date.today().year}/001",
            "date":                       today,
            "borrower_name":             "Sunrise Manufacturing Ltd",
            "facility_amount_ngn_000":    500000,
            "facility_tenor":            "60 months",
            "facility_type":             "Term Loan",
            "overall_risk_rating":       "WATCH",
            "credit_recommendation":     "APPROVE WITH CONDITIONS",
            "routing_authority":         "MANAGEMENT_COMMITTEE",
            "routing_authority_label":   "Management Credit Committee",
            "additional_approvers":      ["Senior Management (PEP-connected director)"],
        },
        "sections": {
            "s01_executive_summary": (
                "Sunrise Manufacturing Ltd (RC-482931) has applied for a NGN 500,000,000 Term Loan "
                "facility with a tenor of 60 months to finance the expansion of its food and beverage "
                "manufacturing capacity in Lagos. The overall credit risk is rated WATCH with a "
                "recommendation to APPROVE WITH CONDITIONS, subject to three pre-disbursement conditions "
                "relating to collateral adequacy, key man insurance, and enhanced due diligence sign-off. "
                "This application is routed to the Management Credit Committee."
            ),
            "s02_obligor_profile": (
                "Sunrise Manufacturing Ltd is a private limited company incorporated in Nigeria "
                "(CAC RC-482931) with its registered office in Lagos, Nigeria. The company operates "
                "in the food and beverage manufacturing sector and has been a customer of the Bank "
                "for eight years. The ownership structure consists of two principal shareholders: "
                "Mr Chidi Okonkwo (Managing Director, 65%) and Ms Adaeze Nwosu (Executive Director "
                "Finance, 35%). The group has no subsidiaries or affiliated entities with existing "
                "banking facilities."
            ),
            "s03_purpose_of_credit": (
                "The Borrower seeks a NGN 500,000,000 term loan to finance the acquisition and "
                "installation of food processing equipment and the expansion of its manufacturing "
                "facility at Apapa, Lagos. The expansion is projected to increase production capacity "
                "by 40% and enable the Borrower to meet growing demand from its distribution network "
                "across South-West Nigeria. The purpose is consistent with the Bank's policy on "
                "manufacturing sector lending."
            ),
            "s04_facility_structure": (
                "Facility Type: Term Loan. Principal Amount: NGN 500,000,000. Tenor: 60 months. "
                "Repayment: Equal monthly instalments of principal and interest. "
                "Pricing: MPR + 5.5% per annum (variable). Moratorium: 6 months on principal. "
                "Drawdown: Single drawdown upon satisfaction of all conditions precedent. "
                "Purpose: Capital expenditure for manufacturing capacity expansion."
            ),
            "s05_financial_analysis": (
                "The Borrower's financial performance is rated SATISFACTORY. The base case Debt Service "
                "Coverage Ratio (DSCR) of 1.38x in Year 1 provides adequate coverage above the Bank's "
                "1.20x policy minimum, though headroom is limited under the 15% revenue stress scenario "
                "which produces a DSCR of 1.05x in Year 1. The leverage ratio (D/E: 1.84x) is within "
                "policy limits and the current ratio of 1.42x is satisfactory. Revenue has grown at a "
                "12.4% CAGR over three years. The primary repayment source is assessed as ADEQUATE "
                "subject to the covenant framework recommended herein."
            ),
            "s06_collateral_security": (
                "The security package as presently constituted covers 109.1% of the facility against "
                "the Bank's minimum requirement of 150% for term loans exceeding 3 years. This "
                "represents a shortfall of NGN 204,500,000 in adjusted security value. The primary "
                "security comprises a first legal mortgage over the Apapa warehouse property "
                "(OMV: NGN 420,000,000) and a fixed and floating charge over all assets of the "
                "Borrower. The additional security required to cure the shortfall and the Governor's "
                "Consent on the warehouse property are designated as conditions precedent to drawdown."
            ),
            "s07_kyc_compliance": (
                "The Borrower and its directors have been screened against OFAC, OpenSanctions, and "
                "the Bank's internal watchlists with no adverse sanctions matches. The KYC risk "
                "rating is HIGH and the due diligence tier is Enhanced Due Diligence (EDD) due to "
                "the PEP connection of Executive Director Finance (sibling of serving State "
                "Commissioner). EDD has been completed and documented. Senior Management sign-off "
                "is required as an additional approval condition for this credit."
            ),
            "s08_relationship_revenue": (
                "Sunrise Manufacturing Ltd is a SILVER-tier relationship with a composite "
                "relationship score of 7/10. The Bank earned NGN 7,800,000 in gross revenue "
                "from this relationship in the current year, representing year-on-year growth "
                "of 12.4%. The current Return on Assets (ROA) is 0.84%, below the Bank's "
                "1.0% GOLD tier threshold. A cross-sell programme targeting deposit mobilisation "
                "and trade finance uptake is identified as a route to GOLD tier designation "
                "within the facility tenor."
            ),
            "s09_industry_analysis": (
                "The Nigerian food and beverage manufacturing sector is assessed as MEDIUM risk "
                "with a STABLE outlook. Near-term headwinds from Naira devaluation-driven input "
                "cost inflation (30–40% increase in imported raw material costs since 2023) are "
                "partially offset by population-driven demand growth and government backward "
                "integration support programmes. The sector's credit risk implication is NEUTRAL "
                "and no structural sector-level factors are identified that would constrain the "
                "credit decision. The Borrower holds a CHALLENGER competitive position with "
                "an estimated 2.1% market share in its sub-segment."
            ),
            "s10_management_assessment": (
                "The management team receives a SATISFACTORY overall quality rating with a "
                "composite score of 7/10. The Managing Director (18 years sector experience, "
                "Tier 1 manufacturing background) provides strong strategic leadership, "
                "supported by a Fellow ICAN Finance Director and a former CBN Deputy Director "
                "as independent NED. A key man risk is identified: the MD concentrates all "
                "operational and client relationships with no documented succession plan. "
                "Key man life and disability insurance and a Board succession plan are "
                "designated as conditions precedent to drawdown."
            ),
            "s11_risk_assessment": (
                "The overall credit risk is rated WATCH across six dimensions. The two most "
                "material risks are: (1) Collateral shortfall of NGN 204.5m against the 150% "
                "minimum requirement (VERY HIGH pre-mitigation; LOW post additional security); "
                "and (2) Key man concentration in the MD (HIGH pre-mitigation; MEDIUM post "
                "insurance and succession plan). Secondary risks include the PEP-connected "
                "director (MEDIUM; mitigated by EDD completion) and FX input cost pressure "
                "(MEDIUM; partially mitigated by domestic sourcing programmes). The residual "
                "risk profile after the conditions precedent are satisfied is consistent with "
                "a WATCH rating and an APPROVE WITH CONDITIONS recommendation."
            ),
            "s12_conditions_precedent": [
                "Additional security of minimum NGN 204.5m pledged to bring total coverage to 150%",
                "Governor's Consent obtained and first legal mortgage registered on Apapa warehouse",
                "Key man life and disability insurance policy — bank as beneficiary, sum insured = NGN 500m",
                "Senior management sign-off on EDD documentation for PEP-connected director",
                "Board succession plan for the MD submitted to the Bank before first drawdown",
            ],
            "s13_financial_covenants": [
                "DSCR >= 1.20x measured semi-annually throughout the facility tenor",
                "Maximum leverage: Total Debt / EBITDA <= 3.5x throughout the tenor",
                "Minimum cash balance: 3 months of debt service to be maintained at all times",
                "Accounts domiciliation: primary operating accounts to be maintained with the Bank",
                "Negative pledge: no additional charge over collateral assets without Bank consent",
                "Pari passu: no new senior unsecured borrowing without Bank consent",
                "Audit committee to be established within 90 days of first drawdown",
            ],
            "s14_monitoring_reporting": [
                "Semi-annual management accounts within 60 days of each 30 June and 31 December",
                "Annual audited financial statements within 120 days of financial year end",
                "Annual collateral revaluation by a CBN-approved independent valuer",
                "Director change notification to the Bank within 5 business days of any change",
                "Annual KYC refresh including full EDD review given PEP-connected director",
                "Semi-annual covenant compliance certificate signed by Finance Director",
            ],
            "s15_routing_authority": (
                "This credit application is routed to the Management Credit Committee for approval. "
                "The routing is determined by the facility amount (NGN 500,000,000) falling within "
                "the NGN 500M–2B band applicable to the Management Credit Committee under the Bank's "
                "credit approval authority framework. An additional Senior Management sign-off is "
                "required prior to committee presentation due to the PEP connection of the Executive "
                "Director Finance."
            ),
            "s16_recommendation": (
                "The Credit Department recommends APPROVAL WITH CONDITIONS of the NGN 500,000,000 "
                "Term Loan facility for Sunrise Manufacturing Ltd, subject to the five conditions "
                "precedent set out in Section 12 being fully satisfied before any drawdown is "
                "permitted. The financial performance, industry position, and management quality "
                "are each assessed as satisfactory, and the identified risks are assessed as "
                "resolvable within the proposed conditions framework."
            ),
        },
        "_metadata": {
            "mode": "mock", "model": None,
            "input_tokens": 0, "output_tokens": 0, "estimated_cost_usd": 0.0
        },
    }
 
 
# ─────────────────────────────────────────────────────
# HTML MEMO GENERATOR
# ─────────────────────────────────────────────────────
 
def generate_html_memo(result: dict) -> str:
    """Convert JSON memo result into a print-ready HTML document."""
    meta = result.get("memo_metadata", {})
    secs = result.get("sections", {})
 
    borrower   = meta.get("borrower_name", "The Borrower")
    ref        = meta.get("memo_reference", "—")
    memo_date  = meta.get("date", str(date.today()))
    amount     = meta.get("facility_amount_ngn_000", 0)
    rating     = meta.get("overall_risk_rating", "—")
    rec        = meta.get("credit_recommendation", "—")
    routing    = meta.get("routing_authority_label", "—")
    addl       = meta.get("additional_approvers", [])
 
    amount_str = f"NGN {amount:,.0f}k" if amount else "—"
 
    rating_color = {
        "PASS": "#1A6B3C", "WATCH": "#854F0B",
        "SUBSTANDARD": "#C45C0A", "DOUBTFUL": "#A32D2D", "DECLINE": "#6B1212",
    }.get(rating, "#333")
 
    rec_color = "#1A6B3C" if "APPROVE" in rec and "CONDITION" not in rec else \
               "#854F0B" if "CONDITION" in rec else "#A32D2D"
 
    list_items = lambda items: "".join(f"<li>{i}</li>" for i in (items or []))
 
    section_html = ""
    section_defs = [
        ("01", "Executive Summary",         secs.get("s01_executive_summary", "")),
        ("02", "Obligor Profile",            secs.get("s02_obligor_profile", "")),
        ("03", "Purpose of Credit",          secs.get("s03_purpose_of_credit", "")),
        ("04", "Facility Structure",         secs.get("s04_facility_structure", "")),
        ("05", "Financial Analysis",         secs.get("s05_financial_analysis", "")),
        ("06", "Collateral & Security",      secs.get("s06_collateral_security", "")),
        ("07", "KYC & AML Compliance",       secs.get("s07_kyc_compliance", "")),
        ("08", "Relationship & Revenue",     secs.get("s08_relationship_revenue", "")),
        ("09", "Industry Analysis",          secs.get("s09_industry_analysis", "")),
        ("10", "Management Assessment",      secs.get("s10_management_assessment", "")),
        ("11", "Risk Assessment & Mitigants",secs.get("s11_risk_assessment", "")),
    ]
    for num, title, content in section_defs:
        if content:
            section_html += f"""
            <div class="section">
              <div class="section-header">
                <span class="section-num">{num}</span>
                <span class="section-title">{title}</span>
              </div>
              <p class="section-content">{content}</p>
            </div>"""
 
    cps  = list_items(secs.get("s12_conditions_precedent", []))
    covs = list_items(secs.get("s13_financial_covenants", []))
    mons = list_items(secs.get("s14_monitoring_reporting", []))
 
    return f"""<!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width,initial-scale=1">
      <title>Credit Approval Memo — {borrower}</title>
      <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: 'Inter', Arial, sans-serif; font-size: 11pt;
               color: #2C2C2A; background: #fff; padding: 40px; max-width: 900px;
               margin: 0 auto; }}
        .header {{ border-bottom: 3px solid #161E41; padding-bottom: 16px; margin-bottom: 24px; }}
        .bank-name {{ font-size: 22pt; font-weight: 700; color: #161E41; }}
        .bank-name span {{ color: #1D63EB; }}
        .memo-title {{ font-size: 14pt; font-weight: 700; color: #161E41;
                      margin: 8px 0 4px; letter-spacing: 1px; }}
        .meta-grid {{ display: grid; grid-template-columns: 1fr 1fr;
                     gap: 8px 24px; margin: 20px 0; }}
        .meta-item {{ display: flex; gap: 8px; }}
        .meta-label {{ font-weight: 600; color: #5F5E5A; min-width: 130px; font-size: 10pt; }}
        .meta-value {{ color: #2C2C2A; font-size: 10pt; }}
        .stamp-row {{ display: flex; gap: 16px; margin: 20px 0; }}
        .stamp {{ padding: 10px 20px; border-radius: 6px; font-weight: 700;
                 font-size: 11pt; border: 2px solid; text-align: center; }}
        .stamp-rating {{ color: {rating_color}; border-color: {rating_color};
                        background: {rating_color}18; }}
        .stamp-rec {{ color: {rec_color}; border-color: {rec_color};
                     background: {rec_color}18; }}
        .stamp-route {{ color: #161E41; border-color: #161E41; background: #E6F1FB; }}
        .section {{ margin: 20px 0; page-break-inside: avoid; }}
        .section-header {{ display: flex; align-items: center; gap: 12px;
                          border-left: 4px solid #161E41; padding: 8px 12px;
                          background: #F3F2EE; margin-bottom: 10px; }}
        .section-num {{ background: #161E41; color: white; font-weight: 700;
                       font-size: 9pt; padding: 2px 7px; border-radius: 3px; }}
        .section-title {{ font-weight: 700; font-size: 11pt; color: #161E41; }}
        .section-content {{ line-height: 1.7; color: #2C2C2A; padding: 0 8px; }}
        .list-section {{ margin: 20px 0; }}
        .list-section h3 {{ font-size: 11pt; font-weight: 700; color: #161E41;
                           border-left: 4px solid #0F6E56; padding: 8px 12px;
                           background: #E1F5EE; margin-bottom: 10px; }}
        ol {{ padding-left: 24px; line-height: 1.8; }}
        ol li {{ margin-bottom: 4px; }}
        .footer-bar {{ margin-top: 40px; padding-top: 16px;
                      border-top: 2px solid #161E41; font-size: 9pt;
                      color: #5F5E5A; text-align: center; }}
        @media print {{
          body {{ padding: 20px; }}
          .section {{ page-break-inside: avoid; }}
        }}
      </style>
    </head>
    <body>
      <div class="header">
        <div class="bank-name">Incepify<span>AI</span>
          <span style="font-size:11pt;font-weight:400;color:#5F5E5A;margin-left:12px">
          Credit Underwriting Suite</span></div>
        <div class="memo-title">CREDIT APPROVAL MEMORANDUM</div>
      </div>
      <div class="meta-grid">
        <div class="meta-item"><span class="meta-label">Memo Reference:</span>
          <span class="meta-value">{ref}</span></div>
        <div class="meta-item"><span class="meta-label">Date:</span>
          <span class="meta-value">{memo_date}</span></div>
        <div class="meta-item"><span class="meta-label">Borrower:</span>
          <span class="meta-value"><strong>{borrower}</strong></span></div>
        <div class="meta-item"><span class="meta-label">Facility Amount:</span>
          <span class="meta-value"><strong>{amount_str}</strong></span></div>
        <div class="meta-item"><span class="meta-label">Tenor:</span>
          <span class="meta-value">{meta.get("facility_tenor","—")}</span></div>
        <div class="meta-item"><span class="meta-label">Facility Type:</span>
          <span class="meta-value">{meta.get("facility_type","—")}</span></div>
      </div>
      <div class="stamp-row">
        <div class="stamp stamp-rating">RISK: {rating}</div>
        <div class="stamp stamp-rec">{rec}</div>
        <div class="stamp stamp-route">→ {routing}</div>
      </div>
      {section_html}
      <div class="list-section">
        <h3>12 — Conditions Precedent</h3>
        <ol>{cps}</ol>
      </div>
      <div class="list-section">
        <h3>13 — Financial Covenants</h3>
        <ol>{covs}</ol>
      </div>
      <div class="list-section">
        <h3>14 — Monitoring & Reporting</h3>
        <ol>{mons}</ol>
      </div>
      <div class="section">
        <div class="section-header">
          <span class="section-num">15</span>
          <span class="section-title">Routing & Approval Authority</span>
        </div>
        <p class="section-content">{secs.get("s15_routing_authority","")}</p>
        {"<p class='section-content'><strong>Additional approvers required:</strong> " + ", ".join(addl) + "</p>" if addl else ""}
      </div>
      <div class="section" style="background:#FEF6DC;border:2px solid #8B6914;
           padding:16px;border-radius:8px;">
        <div class="section-header" style="background:transparent;border-left-color:#8B6914;">
          <span class="section-num" style="background:#8B6914;">16</span>
          <span class="section-title" style="color:#5A4309;">Overall Recommendation</span>
        </div>
        <p class="section-content" style="font-weight:600;">{secs.get("s16_recommendation","")}</p>
      </div>
      <div class="footer-bar">
        IncepifyAI Credit Underwriting Suite  ·  {ref}  ·  Generated {memo_date}
        <br>This document is AI-assisted. All final credit decisions rest with the approving authority.
      </div>
    </body>
    </html>"""
 
 
# ─────────────────────────────────────────────────────
# CLAUDE API CALL — SINGLE CALL, NO AGENTIC LOOP
# ─────────────────────────────────────────────────────
 
def _run_claude_analysis(all_outputs: dict) -> dict:
    """Single Claude call to write the complete memo."""
    if client is None:
        r = get_mock_report_result()
        r["_metadata"]["error"] = "ANTHROPIC_API_KEY not set."
        return r
 
    user_message = (
        "Assemble the complete credit approval memo for the following application.\n\n"
        "ALL AGENT OUTPUTS:\n"
        f"{json.dumps(all_outputs, indent=2, default=str)}\n\n"
        "Write the full 16-section memo. Return ONLY the JSON."
    )
 
    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=12000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )
        text = next(
            (b.text for b in response.content if getattr(b,"type",None)=="text"), ""
        )
        result = _parse_json(text)
        result["_metadata"] = {
            "mode":               "claude",
            "model":              MODEL,
            "input_tokens":       response.usage.input_tokens,
            "output_tokens":      response.usage.output_tokens,
            "estimated_cost_usd": round(
                response.usage.input_tokens  * 0.000003 +
                response.usage.output_tokens * 0.000015, 4
            ),
        }
        return result
    except Exception as exc:
        r = get_mock_report_result()
        r["_metadata"]["error"] = f"{type(exc).__name__}: {exc}"
        return r
 
 
def _parse_json(text: str) -> dict:
    cleaned = re.sub(r"^```(?:json)?\s*","",text.strip(),flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$","",cleaned.strip()).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        if start == -1:
            raise ValueError(f"No JSON: {text[:200]}")
        depth = 0
        for i, ch in enumerate(cleaned[start:], start=start):
            if ch == "{": depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return json.loads(cleaned[start:i+1])
        raise ValueError("Unbalanced JSON.")
