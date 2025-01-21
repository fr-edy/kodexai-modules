import utilities.logger
import utilities.networking
import utilities.html_parser
import time


class ScrapingFramework:
    def __init__(self, id: str, debug: bool = False) -> None:
        self.debug = debug
        self.logger = utilities.logger.ConsoleLogger(id, self.debug)
        self.client = utilities.networking.Client(self.logger)
        self.client.set_timeout(60).init()

    def retry_wait(self, seconds: int = 2) -> None:
        time.sleep(seconds)
