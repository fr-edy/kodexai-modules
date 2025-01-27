import logging
import requests

log = logging.getLogger(__name__)

HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "de-DE,de;q=0.9,en-DE;q=0.8,en;q=0.7,en-US;q=0.6",
    "Cache-Control": "max-age=0",
    "Connection": "keep-alive",
    "DNT": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
}


def load_page_content(url: str, params: dict = None) -> str:
    log.info(f"Loading link '{url}' with params: {params}")

    for attempt in range(3):
        resp = requests.get(url, headers=HEADERS)
        if resp.ok and resp.content:
            break
        log.warning(
            f"{attempt + 1} - failed to load '{url}' (status {resp.status_code}): {resp.content}"
        )

    else:
        log.error(f"Failed to load link '{url}' after 3 attempts.")
        raise Exception(f"Failed to load link '{url}' after 3 attempts.")

    log.info(
        f"Loaded link '{url}' with status {resp.status_code} and content length {len(resp.text)}"
    )
    return resp.text
