import json
import time
import os
import pdfkit
from jinja2 import Environment, FileSystemLoader
from dotenv import load_dotenv


load_dotenv()


json_file = os.getenv("JSON_FILE_PATH")

if not json_file:
    raise ValueError("❌ JSON_FILE_PATH is not set in .env file!")


while not os.path.exists(json_file):
    print("⏳ Waiting for trial.json to be created...")
    time.sleep(2)


with open(json_file, "r", encoding="utf-8") as file:
    data = json.load(file)


data = data[0] if isinstance(data, list) else data


context = {
    "url": data.get("url", "N/A"),
    "meta_title": data.get("meta_title", "N/A"),
    "meta_description": data.get("meta_description", "N/A"),
    "canonical": data.get("canonical", ""),
    "meta_robots": data.get("meta_robots", ""),
    "h1_tags": data.get("h1_tags", []),
    "h2_tags": data.get("h2_tags", []),
    "h3_tags": data.get("h3_tags", []),
    "h4_tags": data.get("h4_tags", []),
    "h5_tags": data.get("h5_tags", []),
    "h6_tags": data.get("h6_tags", []),
    "internal_links_count": data.get("internal_links_count", 0),
    "internal_links": data.get("internal_links", []),
    "external_links_count": data.get("external_links_count", 0),
    "external_links": data.get("external_links", []),
    "image_data": data.get("image_data", []),
    "structured_data": data.get("structured_data", []),
    "open_graph_data": data.get("open_graph_data", {}),
    "twitter_card_data": data.get("twitter_card_data", {}),
    "hreflang_tags": data.get("hreflang_tags", []),
    "viewport": data.get("viewport", ""),
    "load_time": data.get("load_time", 0),
    "issues_detected": data.get("issues_detected", []),
    "ai_recommendations": data.get("ai_recommendations", {}).get("ai_recommendations", []),
}



env = Environment(loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), "templates")))
template = env.get_template("report_template.html")


html_file_path = os.path.join(os.path.dirname(json_file), "SEO_Audit_Report.html")
pdf_file_path = os.path.join(os.path.dirname(json_file), "SEO_Audit_Report.pdf")


html_output = template.render(context)
with open(html_file_path, "w", encoding="utf-8") as html_file:
    html_file.write(html_output)

print(f"✅ HTML Report Generated: {html_file_path}")


pdfkit.from_file(html_file_path, pdf_file_path)

print(f"✅ PDF Report Generated: {pdf_file_path}")
