from app.core.config import settings
from app.core.logger import get_logger
from app.db.vector_store import search_documents

logger = get_logger(__name__)


def search_hr_policy(query: str) -> dict:
    logger.info(f"Policy search: {query}")
    results = search_documents(query, n_results=settings.top_k_results)
    if not results:
        return {
            "found": False,
            "message": "No policy documents found. Run `python -m scripts.ingest` first.",
            "results": [],
        }
    formatted = [
        {
            "content": r["content"],
            "policy": r["metadata"].get("policy_name", "Unknown"),
            "section": r["metadata"].get("section", ""),
        }
        for r in results
    ]
    return {"found": True, "results": formatted}
