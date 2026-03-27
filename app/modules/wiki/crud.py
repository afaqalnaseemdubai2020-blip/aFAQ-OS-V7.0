"""
Wiki CRUD — in-memory storage for now, swap to DB later.
"""
from typing import List, Optional
from datetime import datetime
from app.modules.wiki.models import (
    WikiArticleCreate, WikiArticleResponse, WikiArticleUpdate, ArticleStatus
)
from app.modules.wiki.nlp import arabic_nlp

class WikiCRUD:
    def __init__(self):
        self._articles: dict = {}
        self._counter = 0

    async def create(self, article: WikiArticleCreate) -> WikiArticleResponse:
        self._counter += 1
        now = datetime.utcnow()
        
        # Auto-extract keywords
        text_for_keywords = article.content_ar if article.content_ar else article.content
        keywords = arabic_nlp.extract_keywords(text_for_keywords, max_keywords=10)
        
        # Shape Arabic text if RTL
        shaped = None
        if article.is_rtl and article.content_ar:
            shaped = arabic_nlp.shape_arabic(article.content_ar)
        
        self._articles[self._counter] = {
            "id": self._counter,
            "title": article.title,
            "title_ar": article.title_ar,
            "content": article.content,
            "content_ar": article.content_ar,
            "tags": article.tags,
            "keywords": keywords,
            "category": article.category,
            "status": ArticleStatus.PUBLISHED,
            "is_rtl": article.is_rtl,
            "created_at": now,
            "updated_at": now,
            "shaped_text": shaped
        }
        return WikiArticleResponse(**self._articles[self._counter])

    async def list_all(self, category=None, tag=None, search=None, limit=50) -> List[WikiArticleResponse]:
        results = list(self._articles.values())
        if category:
            results = [a for a in results if a["category"] == category]
        if tag:
            results = [a for a in results if tag in a["tags"]]
        if search:
            search_lower = search.lower()
            results = [a for a in results if search_lower in a["title"].lower() or search_lower in a["content"].lower()]
        return [WikiArticleResponse(**a) for a in results[:limit]]

    async def get_by_id(self, article_id: int) -> Optional[WikiArticleResponse]:
        article = self._articles.get(article_id)
        return WikiArticleResponse(**article) if article else None

    async def update(self, article_id: int, update: WikiArticleUpdate) -> Optional[WikiArticleResponse]:
        if article_id not in self._articles:
            return None
        article = self._articles[article_id]
        for key, value in update.dict(exclude_unset=True).items():
            article[key] = value
        article["updated_at"] = datetime.utcnow()
        
        # Re-extract keywords if content changed
        if update.content or update.content_ar:
            text = article.get("content_ar") or article["content"]
            article["keywords"] = arabic_nlp.extract_keywords(text, max_keywords=10)
        
        return WikiArticleResponse(**article)

    async def delete(self, article_id: int) -> bool:
        if article_id in self._articles:
            del self._articles[article_id]
            return True
        return False

wiki_crud = WikiCRUD()
