from ddgs import DDGS
import logging
import time

logger = logging.getLogger(__name__)

def web_search(query: str, max_results: int = 3) -> str:
    """
    Search the web for current/real-time information.
    Use this when user asks about recent news, current events,
    or anything not in HR documents.
    """
    try:
        logger.info(f"Web search query: {query}")

        for attempt in range(3):
            try:
                with DDGS() as ddgs:
                    results = list(ddgs.text(query, max_results=max_results))
                break
            except Exception as retry_err:
                logger.warning(f"Attempt {attempt + 1} failed: {retry_err}")
                time.sleep(1)
        else:
            return "Web search failed after 3 attempts. Please try again."

        if not results:
            return "No results found on the web."

        output = []
        for i, r in enumerate(results, 1):
            output.append(
                f"Result {i}:\n"
                f"Title: {r['title']}\n"
                f"Content: {r['body']}\n"  
                f"Source: {r['href']}"
            )

        final = "\n\n".join(output)

        summary = f"Found {len(results)} web results for: '{query}'\n\n"

        logger.info(f"Web search completed: {len(results)} results found")
        return summary + final

    except Exception as e:
        logger.error(f"Web search failed: {e}")
        return f"Web search error: {str(e)}"


if __name__ == "__main__":
    result = web_search("latest AI news 2026")
    print(result)