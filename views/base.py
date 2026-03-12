from math import e
from fastapi import APIRouter, Request, Depends, Query, HTTPException
from core.lax.template_parser import TemplateParser
from fastapi.responses import HTMLResponse
from core.db import DB
from core.models.feed import Feed
from core.models.article import Article
from driver.wxarticle import Web
from datetime import datetime


def get_mps_view(
    page: int,
    limit: int
):
    session = DB.get_session()
    data={}
    try:
        # 查询公众号总数
        total = session.query(Feed).filter(Feed.status == 1).count()
        
        # 计算偏移量
        offset = (page - 1) * limit

        # 查询公众号列表
        feeds = session.query(Feed).filter(Feed.status == 1).order_by(Feed.created_at.desc()).offset(offset).limit(limit).all()
        
        # 处理公众号数据
        feed_list = []
        for feed in feeds:
            # 对于 Feed 表，id 就是公众号的 ID
            mp_id = feed.id
            
            # 统计该公众号的文章数量
            article_count = session.query(Article).filter(
                Article.mp_id == mp_id,
                Article.status == 1
            ).count()
            
            feed_data = {
                "id": feed.id,
                "name": feed.mp_name,
                "cover": Web.get_image_url(feed.mp_cover) if feed.mp_cover else "",
                "intro": feed.mp_intro,
                "mp_count": 1,  # Feed 本身就是一个公众号
                "article_count": article_count,
                "sync_time": datetime.fromtimestamp(feed.sync_time).strftime('%Y-%m-%d %H:%M') if feed.sync_time else "未同步",
                "created_at": feed.created_at.strftime('%Y-%m-%d') if feed.created_at else ""
            }
            feed_list.append(feed_data)
        
        # 计算分页信息
        total_pages = (total + limit - 1) // limit
        has_prev = page > 1
        has_next = page < total_pages
        
        # 构建面包屑
        breadcrumb = [
            {"name": "公众号", "url": "/views/mps"}
        ]
        data={
            "feeds": feed_list,
            "current_page": page,
            "total_pages": total_pages,
            "total_items": total,
            "limit": limit,
            "has_prev": has_prev,
            "has_next": has_next,
            "breadcrumb": breadcrumb
        }
    except Exception as e:
        print(e)
    finally:
        session.close()
    return data


def _render_template_with_error(template_path: str, error_msg: str, breadcrumb: list) -> HTMLResponse:
    """渲染错误页面的辅助函数"""
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        parser = TemplateParser(template_content, template_dir=base.public_dir)
        html_content = parser.render({
            "site": base.site,
            "error": error_msg,
            "breadcrumb": breadcrumb
        })
        return HTMLResponse(content=html_content)
    except Exception:
        return HTMLResponse(content=f"<h1>系统错误</h1><p>{error_msg}</p>")

def process_content_images(content: str) -> str:
    """处理文章内容中的图片链接，添加前缀"""
    if not content:
        return content
    return Web.proxy_images(content)