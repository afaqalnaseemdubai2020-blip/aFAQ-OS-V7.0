"""
aFAQ-OS Wiki Module — self-registers with module registry.
"""

from datetime import datetime
from app.core.domain.module import ModuleInfo, ModuleStatus
from app.core.module_registry import module_registry
from app.core.feature_flags import feature_flags

# Module metadata
MODULE_INFO = ModuleInfo(
    name="Wiki & Knowledge Base",
    version="7.0.0",
    slug="wiki",
    description="Collaborative wiki with Arabic NLP, versioning, and full-text search.",
    status=ModuleStatus.DISABLED,
    feature_flag_key="wiki",
    icon="📖",
    category="core",
    dependencies=[],
    api_prefix="/api/wiki",
    created_at=datetime(2025, 3, 27),
)

# Enable via feature flag
feature_flags.enable("wiki")

# Self-register
module_registry.register("wiki", MODULE_INFO)

def get_router():
    """Lazy import to avoid circular dependencies."""
    from app.modules.wiki.router import wiki_router
    return wiki_router
