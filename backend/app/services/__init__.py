"""Services package."""

from app.services.analytics_service import (
    get_order_analytics,
    get_campaign_analytics,
    get_consumer_analytics,
    get_feedback_analytics,
)
from app.services.chroma_service import (
    get_chroma_client,
    get_or_create_collection,
    add_documents,
    query_collection,
    delete_collection,
    get_collection_count,
)
from app.services.embedding_service import (
    get_openai_client,
    generate_embeddings_batch,
    generate_embedding_single,
)
from app.services.rag_service import (
    query_chroma,
    get_relevant_context,
    get_context_summary,
)
from app.services.data_loader import (
    load_store_data,
    load_orders_data,
    load_campaigns_data,
    load_campaign_results_data,
    load_consumers_data,
    load_consumer_preferences_data,
    load_feedbacks_data,
    load_menu_events_data,
    load_all_data,
)
from app.services.document_compiler import (
    compile_all_documents_for_store,
)
from app.services.cache_service import (
    CacheService,
    get_cache_service,
    DEFAULT_INSIGHTS_TTL,
)

__all__ = [
    # Analytics
    "get_order_analytics",
    "get_campaign_analytics",
    "get_consumer_analytics",
    "get_feedback_analytics",
    # Chroma
    "get_chroma_client",
    "get_or_create_collection",
    "add_documents",
    "query_collection",
    "delete_collection",
    "get_collection_count",
    # Embeddings
    "get_openai_client",
    "generate_embeddings_batch",
    "generate_embedding_single",
    # RAG
    "query_chroma",
    "get_relevant_context",
    "get_context_summary",
    # Data loading
    "load_store_data",
    "load_orders_data",
    "load_campaigns_data",
    "load_campaign_results_data",
    "load_consumers_data",
    "load_consumer_preferences_data",
    "load_feedbacks_data",
    "load_menu_events_data",
    "load_all_data",
    # Document compilation
    "compile_all_documents_for_store",
    # Cache
    "CacheService",
    "get_cache_service",
    "DEFAULT_INSIGHTS_TTL",
]
