"""
Wiki Models — article schema, Arabic text fields, keyword metadata.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class ArticleStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"

class WikiArticleCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    title_ar: Optional[str] = Field(None, max_length=500)
    content: str = Field(..., min_length=1)
    content_ar: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    category: Optional[str] = None
    is_rtl: bool = False

class WikiArticleResponse(BaseModel):
    id: int
    title: str
    title_ar: Optional[str]
    content: str
    content_ar: Optional[str]
    tags: List[str]
    keywords: List[str]
    category: Optional[str]
    status: ArticleStatus
    is_rtl: bool
    created_at: datetime
    updated_at: datetime
    shaped_text: Optional[str] = None

class WikiArticleUpdate(BaseModel):
    title: Optional[str] = None
    title_ar: Optional[str] = None
    content: Optional[str] = None
    content_ar: Optional[str] = None
    tags: Optional[List[str]] = None
    category: Optional[str] = None
    is_rtl: Optional[bool] = None
    status: Optional[ArticleStatus] = None

class KeywordExtractRequest(BaseModel):
    text: str
    language: str = "ar"
    max_keywords: int = Field(default=10, ge=1, le=50)
