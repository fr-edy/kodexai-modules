# 🧐 Scraping Test Assignment

Your task is to develop a Python module named `dbb_scraper.py` to scrape information from the [Deutsche Bundesbank (DBB)](https://www.bundesbank.de/de) website. For this assignment, the focus will be on extracting data from the following two sources:

- Stellungsnahmen — [web page](https://www.bundesbank.de/de/presse/stellungnahmen)
- Pressenotizen — [RSS feed](https://www.bundesbank.de/service/rss/de/633286/feed.rss)
  The goal is to extract relevant publications, including their associated metadata (e.g. title and publication date) and links, and implement functionality to download attached files.

## Requirements:

1. Write a standalone Python module compatible with Python 3.10+.
2. Use any necessary libraries or services to complete the task.
3. Implement three core scraping methods from the code template.
4. Ensure your code is robust and handles potential errors such as broken links or bot detection mechanisms.
5. Use Python’s `logging` module to log the execution flow.
6. Submit a link to a public repository on GitHub with your code.

## Notes:

1. `load_rss_link()`
   - Include both web (`web_url`) and file links (`related_urls`).
2. `load_web_link()`
   - If a publication links directly to a **PDF file**, store this in the `web_url` field.
   - If a publication links to a **web article**, store this in the `web_url` field and extract any associated file attachments or related links (see [example page](https://www.bundesbank.de/de/presse/stellungnahmen/schriftliche-stellungnahme-der-deutschen-bundesbank-anlaesslich-des-konsultationsprozesses-der-europaeischen-kommission-zur-ueberpruefung-des-wirtschaftspolitischen-rahmens-der-eu-oktober-bis-dezember-2021-884870)). These should be added to the `related_urls` field.
3. `download_file()`
   - Ensure it can bypass simple bot detection mechanisms.

## Code Template:

```python
from dataclasses import field, dataclass
from datetime import datetime
from io import BytesIO


@dataclass
class Publication:
    web_title: str
    published_at: datetime
    web_url: str
    related_urls: list[str] = field(default_factory=list)


def load_rss_link(rss_url: str) -> list[Publication]:
	pass  # TODO


def load_web_link(web_url: str) -> list[Publication]:
	pass  # TODO


def download_file(file_url: str) -> BytesIO:
	pass  # TODO


# Example usage
if __name__ == "__main__":
	rss_pubs = load_rss_link("https://www.bundesbank.de/service/rss/de/633286/feed.rss")
	web_pubs = load_web_link("https://www.bundesbank.de/de/presse/stellungnahmen")
	pdf_bytes = download_file("https://www.bundesbank.de/resource/blob/696204/ffdf2c3e5dc30961892a835482998453/472B63F073F071307366337C94F8C870/2016-01-11-ogaw-download.pdf")
```
