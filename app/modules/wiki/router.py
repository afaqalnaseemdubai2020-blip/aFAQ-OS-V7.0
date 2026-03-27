"""
Wiki Router — CRUD endpoints, keyword extraction, Arabic text shaping.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from app.modules.wiki.models import (
    WikiArticleCreate, WikiArticleResponse, WikiArticleUpdate, 
    KeywordExtractRequest
)
from app.modules.wiki.crud import wiki_crud
from app.modules.wiki.nlp import arabic_nlp

wiki_router = APIRouter(prefix="/api/wiki", tags=["Wiki"])

@wiki_router.post("/articles", response_model=WikiArticleResponse, status_code=201)
async def create_article(article: WikiArticleCreate):
    """Create wiki article with auto keyword extraction."""
    return await wiki_crud.create(article)

@wiki_router.get("/articles", response_model=List[WikiArticleResponse])
async def list_articles(
    category: Optional[str] = None,
    tag: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=200)
):
    """List wiki articles with optional filters."""
    return await wiki_crud.list_all(category=category, tag=tag, search=search, limit=limit)

@wiki_router.get("/articles/{article_id}", response_model=WikiArticleResponse)
async def get_article(article_id: int):
    """Get single wiki article."""
    article = await wiki_crud.get_by_id(article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article

@wiki_router.put("/articles/{article_id}", response_model=WikiArticleResponse)
async def update_article(article_id: int, update: WikiArticleUpdate):
    """Update wiki article."""
    article = await wiki_crud.update(article_id, update)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article

@wiki_router.delete("/articles/{article_id}")
async def delete_article(article_id: int):
    """Delete wiki article."""
    success = await wiki_crud.delete(article_id)
    if not success:
        raise HTTPException(status_code=404, detail="Article not found")
    return {"deleted": True, "id": article_id}

@wiki_router.post("/extract-keywords")
async def extract_keywords(req: KeywordExtractRequest):
    """Extract keywords using YAKE algorithm."""
    keywords = arabic_nlp.extract_keywords(req.text, req.language, req.max_keywords)
    return {"keywords": keywords, "language": req.language}

@wiki_router.post("/shape-text")
async def shape_text(text: str = Query(...), direction: str = Query("rtl")):
    """Shape Arabic text using HarfBuzz (bidi/RTL handling)."""
    shaped = arabic_nlp.shape_arabic(text)
    return {"original": text, "shaped": shaped, "direction": direction}
