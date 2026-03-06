"""
generate_report.py
------------------
Uses Jinja2 to template the HTML report with brand settings and analysis,
then uses WeasyPrint to export it to a branded PDF.

Reads:  data/business_profile.json
        assets/brand.json
        tmp/analysis_results.json
        assets/report_template.html
Writes: Hacker's_Unity_Competitor_Analysis.pdf
"""

import os
import json
import datetime
from jinja2 import Environment, FileSystemLoader
# Fallback to pure HTML output if WeasyPrint fails (useful on some machines without cairo)
try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False
    print("⚠️ WeasyPrint is not installed or missing dependencies. Will generate HTML instead of PDF.")

def generate_pdf():
    print("🎨 Generating branded report...")

    # Load data
    with open("data/business_profile.json", "r") as f:
        business = json.load(f)
    with open("assets/brand.json", "r") as f:
        brand = json.load(f)
    try:
        with open("tmp/analysis_results.json", "r") as f:
            analysis = json.load(f)
    except FileNotFoundError:
        print("❌ Error: tmp/analysis_results.json not found. Run analysis first.")
        return

    # Set up Jinja2 environment
    import urllib.parse
    env = Environment(loader=FileSystemLoader("assets"))
    template = env.get_template("report_template.html")

    # Resolve absolute path for the logo so WeasyPrint can find it
    logo_path = "assets/logo.png"
    if not os.path.exists(logo_path):
        # We'll just use an empty string or it will show broken image
        logo_abs_path = ""
        print(f"⚠️ Warning: Logo not found at {logo_path}")
    else:
        logo_abs_path = "file://" + urllib.parse.quote(os.path.abspath(logo_path))

    # Render HTML string
    html_out = template.render(
        business=business,
        brand=brand,
        analysis=analysis,
        date=datetime.datetime.now().strftime("%B %d, %Y"),
        logo_abs_path=logo_abs_path
    )

    # Output filenames
    safe_name = business['name'].replace(' ', '_').replace("'", "")
    html_filename = f"tmp/{safe_name}_Report.html"
    pdf_filename = f"{safe_name}_Competitor_Analysis.pdf"

    # Always save the HTML version just in case
    with open(html_filename, "w", encoding="utf-8") as f:
        f.write(html_out)

    if WEASYPRINT_AVAILABLE:
        print(f"📄 Converting to PDF: {pdf_filename}...")
        try:
            HTML(string=html_out, base_url=os.path.abspath(".")).write_pdf(pdf_filename)
            print(f"✅ Success! PDF saved to {os.getcwd()}/{pdf_filename}")
        except Exception as e:
            print(f"❌ Error during PDF generation: {e}")
            print(f"✅ HTML fallback available at: {html_filename}")
    else:
        print(f"✅ Success! Since WeasyPrint is unavailable, HTML report saved to {html_filename}")
        print("   (To get a PDF, open the HTML file in Chrome/Edge and choose 'Print -> Save as PDF')")

if __name__ == "__main__":
    generate_pdf()
