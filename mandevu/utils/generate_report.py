import json
import time
import os
import pdfkit
from jinja2 import Environment, FileSystemLoader
from dotenv import load_dotenv
from urllib.parse import urlparse

load_dotenv()

json_file = os.getenv("JSON_FILE_PATH")

if not json_file:
    raise ValueError("JSON_FILE_PATH is not set in .env file!")

# Wait for the file to be created
while not os.path.exists(json_file):
    print("⏳ Waiting for trial.json to be created...")
    time.sleep(2)

with open(json_file, "r", encoding="utf-8") as file:
    data = json.load(file)

if not isinstance(data, list):
    data = [data]

env = Environment(loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), "templates")))
template = env.get_template("report_template.html")

# Create results folder if it doesn't exist
results_dir = os.path.join(os.path.dirname(json_file), "results")
os.makedirs(results_dir, exist_ok=True)

for index, entry in enumerate(data, start=1):
    print(f"📄 Processing Entry {index}/{len(data)}...")

    url = entry.get("url", "N/A")

    # Parse URL to extract a valid page name
    parsed_url = urlparse(url)
    page_name = parsed_url.path.strip("/").replace("/", "_") or "index"  # Use "index" if homepage

    # Remove query parameters and special characters
    page_name = page_name.split("?")[0].split("#")[0]
    page_name = "".join(c if c.isalnum() or c in ["_", "-"] else "_" for c in page_name)

    context = {
        "url": url,
        "meta_title": entry.get("meta_title", "N/A"),
        "meta_description": entry.get("meta_description", "N/A"),
        "canonical": entry.get("canonical", ""),
        "meta_robots": entry.get("meta_robots", ""),
        "h1_tags": entry.get("h1_tags", []),
        "h2_tags": entry.get("h2_tags", []),
        "h3_tags": entry.get("h3_tags", []),
        "h4_tags": entry.get("h4_tags", []),
        "h5_tags": entry.get("h5_tags", []),
        "h6_tags": entry.get("h6_tags", []),
        "internal_links_count": entry.get("internal_links_count", 0),
        "internal_links": entry.get("internal_links", []),
        "external_links_count": entry.get("external_links_count", 0),
        "external_links": entry.get("external_links", []),
        "image_data": entry.get("image_data", []),
        "structured_data": entry.get("structured_data", []),
        "open_graph_data": entry.get("open_graph_data", {}),
        "twitter_card_data": entry.get("twitter_card_data", {}),
        "hreflang_tags": entry.get("hreflang_tags", []),
        "viewport": entry.get("viewport", ""),
        "load_time": entry.get("load_time", 0),
        "issues_detected": entry.get("issues_detected", []),
        "ai_recommendations": entry.get("ai_recommendations", {}).get("ai_recommendations", []),
    }

    # Define paths for HTML and PDF reports using page_name
    html_file_path = os.path.join(results_dir, f"SEO_Audit_Report_{page_name}.html")
    pdf_file_path = os.path.join(results_dir, f"SEO_Audit_Report_{page_name}.pdf")

    # Render HTML report
    html_output = template.render(context)
    with open(html_file_path, "w", encoding="utf-8") as html_file:
        html_file.write(html_output)

    print(f"✅ HTML Report Generated: {html_file_path}")

    # Convert to PDF
    pdfkit.from_file(html_file_path, pdf_file_path)

    print(f"📑 PDF Report Generated: {pdf_file_path}")

print("🎉 All reports generated successfully!")
