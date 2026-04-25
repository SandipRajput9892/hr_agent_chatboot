import chromadb
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)
COLLECTION_NAME = "hr_policies"

_client = None
_collection = None


def get_client() -> chromadb.PersistentClient:
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=settings.chroma_db_path)
    return _client


def get_collection():
    global _collection
    if _collection is None:
        client = get_client()
        _collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=DefaultEmbeddingFunction(),
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(f"Collection '{COLLECTION_NAME}' ready ({_collection.count()} docs)")
    return _collection


def add_documents(documents: list, metadatas: list, ids: list):
    collection = get_collection()
    collection.upsert(documents=documents, metadatas=metadatas, ids=ids)
    logger.info(f"Upserted {len(documents)} documents")


def search_documents(query: str, n_results: int = 3) -> list:
    collection = get_collection()
    count = collection.count()
    if count == 0:
        return []
    results = collection.query(
        query_texts=[query],
        n_results=min(n_results, count),
    )
    docs = []
    for i, doc in enumerate(results["documents"][0]):
        docs.append(
            {
                "content": doc,
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i],
            }
        )
    return docs