import base
import urllib.parse

from parser import parse_decree


class BafinScraper(base.ScrapingFramework):
    def __init__(self):
        super().__init__("BafinScraper", False)
        self.logger.info("Initialized")
        self.base = "https://www.bafin.de"

    def get_decrees(
        self,
        url: str = "https://www.bafin.de/SiteGlobals/Forms/Suche/Expertensuche_Formular.html",
    ):
        self.logger.info("Getting decrees")
        resp = self.client.get(url)
        if not resp.ok():
            self.logger.error(f"Could not get decrees, retrying ({resp.status_code()})")
            self.retry_wait()
            return self.get_decrees(url=url)

        self.logger.success(f"Status {resp.status_code()}")

        tree = base.utilities.html_parser.HTMLParser(resp.text())
        results = tree.xpath("//div[contains(@class, 'search-result')]")
        for result in results:
            parsed = parse_decree(result)
            url = urllib.parse.urljoin(self.base, parsed.url_frag)

            print(url)
