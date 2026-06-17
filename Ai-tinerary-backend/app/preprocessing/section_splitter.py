import re


def split_markdown_by_h2(markdown_text: str):
    pattern = r"(?=^##\s+.+$)"

    sections = re.split(
        pattern,
        markdown_text,
        flags=re.MULTILINE
    )

    cleaned = []

    for section in sections:
        section = section.strip()

        if not section:
            continue

        lines = section.splitlines()

        title = lines[0].replace("##", "").strip()

        content = "\n".join(lines[1:]).strip()

        if len(content.split()) < 40:
            continue

        cleaned.append({
            "section_title": title,
            "content": content,
        })

    return cleaned