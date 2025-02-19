from markitdown import MarkItDown

md = MarkItDown()  # Set to True to enable plugins


def convert_html(html: str) -> str:
    html_md = md.convert("./output/cleaned.html")

    with open("output/page.md", "w") as f:
        f.write(html_md.text_content)

    return html_md.text_content
