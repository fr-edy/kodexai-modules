import logging

from scrapingbee import ScrapingBeeClient

log = logging.getLogger(__name__)

SCRAPINGBEE_CLIENT = ScrapingBeeClient(api_key="NN5IQCRVIK8SLG950QS92332AVY5DE8QBLQEVOO2EKU4SL7GPK1NNVOBRPSZBT2GN93AS5X3F9N6TL3H")  # TODO: use your ScrapingBee API key for testing


def load_page_content(url: str, params: dict = None) -> str:
    """Fetches the HTML content of a given URL using the ScrapingBee client. Retries up to 3 times if the
    request fails, throws an exception if all attempts fail. You can pass custom ScrapingBee parameters
    if the default ones are not suitable for the page you are trying to scrape."""
    if not params:
        params = {"wait": "5000"}
    log.info(f"Loading link '{url}' with params: {params}")

    for attempt in range(3):
        resp = SCRAPINGBEE_CLIENT.get(url, params=params)
        if resp.ok and resp.content:
            break
        log.warning(f"{attempt + 1} - failed to load '{url}' (status {resp.status_code}): {resp.content}")

    else:
        log.error(f"Failed to load link '{url}' after 3 attempts.")
        raise Exception(f"Failed to load link '{url}' after 3 attempts.")

    resp.encoding = "utf-8"  # Ensure the response is handled as UTF-8
    content = resp.content.decode("utf-8", errors="replace")  # Decode content to UTF-8 with error handling
    log.info(f"Loaded link '{url}' with status {resp.status_code} and content length {len(content)}")
    return content
