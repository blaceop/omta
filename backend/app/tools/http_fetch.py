import re

import httpx


async def fetch_url(url: str) -> str:
    timeout = httpx.Timeout(10.0, connect=5.0)
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()
            text = response.text
    except httpx.HTTPStatusError as exc:
        status_code = exc.response.status_code if exc.response is not None else "unknown"
        return (
            f"FETCH_FAILED\n"
            f"url: {url}\n"
            f"reason: HTTP status error\n"
            f"status_code: {status_code}\n"
            f"message: The requested page could not be fetched."
        )
    except httpx.RequestError as exc:
        return (
            f"FETCH_FAILED\n"
            f"url: {url}\n"
            f"reason: Request error\n"
            f"message: {str(exc)}"
        )

    cleaned = re.sub(r"<[^>]+>", " ", text)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if not cleaned:
        return (
            f"FETCH_FAILED\n"
            f"url: {url}\n"
            f"reason: Empty content\n"
            f"message: The page returned no usable text."
        )
    return cleaned[:5000]
