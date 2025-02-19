from bs4 import BeautifulSoup
import os
import requests
from playwright.async_api import async_playwright
from convert import convert_html


async def clean_html(html_content):
    # 使用 BeautifulSoup 加载 HTML
    soup = BeautifulSoup(html_content, "html.parser")

    # 查找所有的iframe标签
    iframes = soup.find_all('iframe')

    # 使用 Playwright 加载 iframe 内容
    async with async_playwright() as p:
        # 启动浏览器
        # headless=True 表示无头模式
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        for iframe in iframes:
            src = iframe.get('src')
            if src:
                try:
                    # 导航到 iframe 的 URL
                    await page.goto(src, wait_until="networkidle")  # 等待页面完全加载
                    # 获取加载后的 HTML 内容
                    iframe_content = await page.content()
                    # 将 iframe 替换为加载后的 HTML 内容
                    iframe.replace_with(BeautifulSoup(
                        iframe_content, 'html.parser'))
                except Exception as e:
                    print(f"Failed to load iframe content from {src}: {e}")
                finally:
                    # 关闭页面
                    await page.close()

        # 关闭浏览器
        await browser.close()

    # 删除所有 img 标签
    for img in soup.find_all("img"):
        img.decompose()

    # 删除所有 style 标签
    for style in soup.find_all("style"):
        style.decompose()

    # 删除所有 script 标签
    for script in soup.find_all("script"):
        script.decompose()

    # 删除所有属性
    for tag in soup.find_all(True):  # True is used to match all tags
        for attribute in list(tag.attrs):
            del tag[attribute]

    # 删除所有注释
    for comment in soup.find_all(string=lambda text: isinstance(text, str) and text.startswith("<!--")):
        comment.extract()

    # 删除所有空白节点
    for tag in soup.find_all(True):  # True is used to match all tags
        if tag.string and tag.string.strip() == "":
            tag.decompose()

    # 写出 HTML
    os.makedirs("output", exist_ok=True)
    with open("output/cleaned.html", "w", encoding="utf-8") as f:
        f.write(soup.prettify())

    return str(soup)


# Example usage
# 读入html测试文件
# with open("test.html", "r", encoding="utf-8") as f:
#     html_content = f.read()
# cleaned_html = clean_html(html_content)
# html_md = convert_html(cleaned_html)
