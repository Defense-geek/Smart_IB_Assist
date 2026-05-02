# html_report_generator.py (renamed from pdf_report_generator.py)

import os
import json
import datetime

from agentic_company_research import call_gemini

# =========================================================
# CONFIG
# =========================================================

from kivy.utils import platform

if platform == "android":
    REPORT_DIR = "/sdcard/SMART_IB_ASSIST/reports"
else:
    REPORT_DIR = "reports"

os.makedirs(REPORT_DIR, exist_ok=True)

# =========================================================
# GEMINI REPORT WRITER
# =========================================================

def generate_final_report_text(report_data: dict, report_type: str) -> str:
    """
    Gemini writes the COMPLETE final report text.
    """

    prompt = f"""
You are a senior investment banking analyst.

TASK:
Write a PROFESSIONAL investment research memo.

STYLE:
- Formal business tone
- Clear headings
- Concise paragraphs
- Bullet points where appropriate
- Natural flow (not templated)
- Explain differences clearly when comparing companies

IMPORTANT RULES:
- Do NOT mention missing data
- Do NOT mention inferred or estimated data
- Do NOT include disclaimers
- Do NOT reference JSON or sources
- Assume exploratory analysis is acceptable
- Be decisive and useful

Report type: {report_type}

INPUT DATA:
{json.dumps(report_data, indent=2)}

WRITE THE COMPLETE REPORT TEXT.
"""

    text = call_gemini(prompt)
    return text.strip()


# =========================================================
# HTML RENDERER
# =========================================================

def generate_html_from_text(final_text: str, output_name: str, report_type: str) -> str:
    """
    Renders Gemini-generated text into an HTML file.
    """

    path = os.path.join(REPORT_DIR, f"{output_name}.html")
    
    # Convert text to HTML paragraphs
    html_content = ""
    for block in final_text.split("\n\n"):
        block = block.strip()
        if block:
            # Check if it's a heading (starts with # or **)
            if block.startswith("# ") or block.startswith("## ") or block.startswith("### "):
                level = block.count("#", 0, 4)
                text = block.lstrip("# ").strip()
                html_content += f"<h{level}>{text}</h{level}>\n"
            elif block.startswith("**") and block.endswith("**"):
                text = block.strip("*")
                html_content += f"<h3>{text}</h3>\n"
            elif block.startswith("- ") or block.startswith("• "):
                items = block.split("\n")
                html_content += "<ul>\n"
                for item in items:
                    item_text = item.lstrip("-•* ").strip()
                    if item_text:
                        html_content += f"  <li>{item_text}</li>\n"
                html_content += "</ul>\n"
            else:
                # Regular paragraph
                html_content += f"<p>{block.replace(chr(10), '<br>')}</p>\n"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SMART-IB-ASSIST Report</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            text-align: justify;        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #e8e8e8;
            line-height: 1.7;
            padding: 20px;
            min-height: 100vh;
            text-align: justify;
        }}
        .container {{
            max-width: 800px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 16px;
            padding: 30px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid rgba(74, 144, 226, 0.5);
        }}
        .header h1 {{
            color: #4a90e2;
            font-size: 24px;
            margin-bottom: 8px;
        }}
        .header .meta {{
            color: #888;
            font-size: 13px;
        }}
        h1, h2, h3 {{
            color: #4a90e2;
            margin: 24px 0 12px 0;
        }}
        h1 {{ font-size: 22px; }}
        h2 {{ font-size: 18px; color: #5cb85c; }}
        h3 {{ font-size: 16px; color: #f0ad4e; }}
        p {{
            margin: 12px 0;
            text-align: justify;
        }}
        ul {{
            margin: 12px 0 12px 24px;
        }}
        li {{
            margin: 6px 0;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
            text-align: center;
            color: #666;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏦 SMART-IB-ASSIST</h1>
            <div class="meta">
                <strong>{report_type}</strong><br>
                Generated: {datetime.date.today()}
            </div>
        </div>
        
        <div class="content">
            {html_content}
        </div>
        
        <div class="footer">
            Generated by SMART-IB-ASSIST • AI-Powered Investment Research
        </div>
    </div>
</body>
</html>
"""

    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    
    return path


# =========================================================
# SINGLE ENTRY POINT (USE THIS)
# =========================================================

def generate_ai_report(
    report_data: dict,
    report_type: str,
    output_name: str
) -> str:
    """
    One-call report generator. Returns path to HTML file.
    """

    final_text = generate_final_report_text(
        report_data=report_data,
        report_type=report_type
    )

    return generate_html_from_text(
        final_text=final_text,
        output_name=output_name,
        report_type=report_type
    )


# =========================================================
# OPTIONAL TEST
# =========================================================
if __name__ == "__main__":
    sample_data = {
        "example": "Replace this with investor_guided_discovery() output"
    }

    html_path = generate_ai_report(
        report_data=sample_data,
        report_type="Investor-Guided Discovery",
        output_name="Sample_Report"
    )

    print("HTML generated at:", html_path)
