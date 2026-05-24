from pathlib import Path
from playwright.sync_api import sync_playwright

from app.services.luxia_parse import parse_document

RAW_WEB_DIR = Path("app/data/web_raw")
OUTPUT_DIR = Path("app/data/cleaned_md")

RAW_WEB_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def safe_filename(url: str):
    return (
        url.replace("https://", "")
        .replace("http://", "")
        .replace("/", "_")
        .replace("?", "_")
        .replace("&", "_")
    )


def download_rendered_html(url: str, output_path: Path):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        page = browser.new_page(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        )

        page.goto(url, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(3000)

        html = page.content()

        output_path.write_text(html, encoding="utf-8")

        browser.close()


def main():
    url = input("Website URL: ").strip()

    filename = safe_filename(url)

    html_path = RAW_WEB_DIR / f"{filename}.html"
    output_path = OUTPUT_DIR / f"{filename}.md"

    print("Rendering page with Playwright...")
    download_rendered_html(url, html_path)

    print("Saved rendered HTML:", html_path)

    parsed = parse_document(str(html_path))

    output_path.write_text(parsed, encoding="utf-8")

    print("\n===== SAVED CLEANED MARKDOWN =====")
    print(output_path)


if __name__ == "__main__":
    main()