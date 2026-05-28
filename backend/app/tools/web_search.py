from urllib.parse import quote

import httpx
from bs4 import BeautifulSoup


async def search_web(query: str) -> str:
    search_url = f"https://html.duckduckgo.com/html/?q={quote(query)}"
    timeout = httpx.Timeout(10.0, connect=5.0)

    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            response = await client.get(
                search_url,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
                    )
                },
            )
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        status_code = exc.response.status_code if exc.response is not None else "unknown"
        return (
            f"SEARCH_FAILED\n"
            f"query: {query}\n"
            f"reason: HTTP status error\n"
            f"status_code: {status_code}"
        )
    except httpx.RequestError as exc:
        return (
            f"SEARCH_FAILED\n"
            f"query: {query}\n"
            f"reason: Request error\n"
            f"message: {str(exc)}"
        )

    soup = BeautifulSoup(response.text, "html.parser")
    results: list[str] = []

    for result in soup.select(".result"):
        title_node = result.select_one(".result__title")
        link_node = result.select_one(".result__url")
        snippet_node = result.select_one(".result__snippet")

        title = title_node.get_text(" ", strip=True) if title_node else "Untitled"
        link = link_node.get_text(" ", strip=True) if link_node else ""
        snippet = snippet_node.get_text(" ", strip=True) if snippet_node else ""

        if title or link or snippet:
            results.append(
                f"Title: {title}\nURL: {link}\nSnippet: {snippet}"
            )

        if len(results) >= 5:
            break

    if not results:
        return (
            f"SEARCH_FAILED\n"
            f"query: {query}\n"
            f"reason: No results\n"
            f"message: No search results were parsed from the response."
        )

    return f"Search results for: {query}\n\n" + "\n\n".join(results)
