import copy
from core.models.article import Article

def fix_content(content: str):
    """将原始 HTML 内容转换为清理后的 HTML 和 Markdown，返回 (html, markdown)"""
    from core.content_format import format_content
    from tools.mdtools.md2html import convert_markdown_to_html
    from tools.htmltools import htmltools
    htmltools.clean_html(content, remove_attributes=[{'src': ''}],remove_ids=['content_bottom_interaction', 'activity-name', 'meta_content'])
    content_markdown = format_content(content, content_format='markdown')
    content_html = convert_markdown_to_html(content_markdown)
    return content_html, content_markdown

def fix_html(content: str):
    html, _ = fix_content(content)
    return html

def fix_article(article):
    art = article.to_dict()
    html, md = fix_content(art['content'])
    art['content'] = html
    art['content_markdown'] = md
    return art