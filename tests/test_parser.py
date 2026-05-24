from app.services.luxia_parse import parse_document
from app.preprocessing.clean_html import clean_luxia_html

html = parse_document("app/data/raw/malaysia-2.pdf")

with open("app/data/clean/malaysia_raw.html", "w", encoding="utf-8") as f:
    f.write(html)

cleaned = clean_luxia_html(html)

with open("app/data/clean/malaysia_clean.md", "w", encoding="utf-8") as f:
    f.write(cleaned)

print(cleaned[:3000])
print("\nSaved raw HTML and cleaned Markdown.")