import base


class BafinScraper(base.ScrapingFramework):
    def __init__(self):
        super().__init__("BafinScraper", False)
        self.logger.info("Initialized")
