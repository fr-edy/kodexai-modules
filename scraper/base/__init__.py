import utilities


class ScrapingFramework:
    def __init__(self, id: str, debug: bool = False) -> None:
        self.debug = debug
        self.logger = utilities.logger.ConsoleLogger(id, self.debug)
        self.client = utilities.networking.Client(self.logger)
        self.client.init()
