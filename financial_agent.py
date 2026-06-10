import anthropic
import json
import os
import re
from pathlib import Path
from dotenv import load_dotenv
 
load_dotenv()  # reads your .env file
 
# Load the system prompt from the separate file
SYSTEM_PROMPT = Path("system_prompt.txt").read_text()
 
# Initialise the Anthropic client
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
 
 
def analyze_financials(extracted_text: str,
                       company_name: str = "Unknown Company") -> dict:
    """
    Send extracted financial data to Claude and return structured analysis.
 
    Args:
        extracted_text: Full text extracted from PDF by pdf_extractor.py
        company_name:   Name of the company being analysed
 
    Returns:
        dict: Structured JSON with ratios, flags, sensitivity, memo narrative
    """
    user_message = f"""Analyse the following financial statements for {company_name}.
 
Return ONLY the JSON object — no other text.
 
--- FINANCIAL STATEMENT DATA START ---
{extracted_text}
--- FINANCIAL STATEMENT DATA END ---"""
 
    response = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}]
    )
 
    raw_text = response.content[0].text.strip()
 
    # Parse JSON — with fallback if Claude adds any wrapping text
    try:
        result = json.loads(raw_text)
    except json.JSONDecodeError:
        json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
        else:
            raise ValueError(f"Cannot parse JSON.\nRaw response:\n{raw_text[:500]}")
 
    # Add metadata for cost tracking
    result["_metadata"] = {
        "model_used":           response.model,
        "input_tokens":         response.usage.input_tokens,
        "output_tokens":        response.usage.output_tokens,
        "estimated_cost_usd":   round(
            (response.usage.input_tokens  * 0.000003) +
            (response.usage.output_tokens * 0.000015), 4
        )
    }
    return result
 
 
def get_mock_result() -> dict:
    """
    Hardcoded sample result — use this to build and test the UI
    without spending API credits. Switch to analyze_financials()
    only when the UI is exactly how you want it.
    """
    return {
        "company_summary": {
            "name": "Test Manufacturing Co Ltd",
            "industry": "Manufacturing",
            "financial_year_end": "December 2023",
            "currency": "NGN",
            "years_of_data_available": 3
        },
        "key_ratios": {
            "profitability": {
                "gross_margin_pct": 32.5,
                "net_profit_margin_pct": 8.2,
                "return_on_assets_pct": 6.1,
                "return_on_equity_pct": 14.3,
                "ebitda_margin_pct": 18.7
            },
            "liquidity": {
                "current_ratio": 1.42,
                "quick_ratio": 0.98,
                "cash_ratio": 0.31
            },
            "leverage": {
                "debt_to_equity": 1.84,
                "debt_to_assets": 0.52,
                "interest_coverage": 3.2,
                "net_debt_to_ebitda": 2.1
            },
            "cashflow": {
                "operating_cashflow_000": 284500,
                "free_cashflow_000": 142000,
                "dscr": 1.38,
                "cashflow_to_total_debt": 0.24
            }
        },
        "trend_analysis": {
            "revenue_3yr_cagr_pct": 12.4,
            "ebitda_3yr_cagr_pct": 9.8,
            "revenue_trend": "GROWING",
            "margin_trend": "STABLE",
            "working_capital_trend": "IMPROVING"
        },
        "financial_highlights": {
            "key_strengths": [
                "Consistent revenue growth of 12.4% CAGR over 3 years",
                "Adequate current ratio of 1.42x above minimum threshold",
                "Strong market position in core manufacturing segment"
            ],
            "key_concerns": [
                "Quick ratio 0.98x indicates reliance on inventory liquidation",
                "DSCR of 1.38x provides limited headroom above 1.20x minimum"
            ]
        },
        "risk_flags": [
            {
                "flag": "Quick ratio borderline",
                "severity": "LOW",
                "detail": "Quick ratio 0.98x marginally below 1.0x.",
                "policy_threshold": "Minimum quick ratio 1.00x (bank policy)"
            }
        ],
        "sensitivity_analysis": {
            "base_case": {
                "revenue_growth_assumption_pct": 10.0,
                "dscr_yr1": 1.42, "dscr_yr2": 1.49, "dscr_yr3": 1.57,
                "narrative": "Base case assumes continued growth in line with 3-yr CAGR."
            },
            "downside_case": {
                "revenue_stress_pct": -15.0,
                "dscr_yr1": 1.21, "dscr_yr2": 1.18, "dscr_yr3": 1.24,
                "narrative": "15% stress brings DSCR near threshold in Year 2."
            }
        },
        "credit_recommendation": {
            "overall_assessment": "SATISFACTORY",
            "primary_repayment_viability": "ADEQUATE",
            "narrative_summary": (
                "Test Manufacturing Co Ltd demonstrates satisfactory financial performance "
                "with consistent revenue growth over the review period. The DSCR "
                "of 1.38x provides adequate coverage above the 1.20x minimum, though headroom is "
                "limited under stress scenarios. Liquidity is acceptable with a current ratio of 1.42x. "
                "Credit is considered bankable subject to standard monitoring covenants."
            ),
        },
        "_metadata": {"model_used":"mock","input_tokens":0,"output_tokens":0,
                      "estimated_cost_usd":0.0}
    }
