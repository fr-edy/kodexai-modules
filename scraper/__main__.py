import modules.bundesbank.scraper

if __name__ == "__main__":
    scraper = modules.bundesbank.scraper.BundesbankScraper()
    print(scraper.load_web_link("https://www.bundesbank.de/de/presse/stellungnahmen"))
    print(scraper.load_rss_link("https://www.bundesbank.de/service/rss/de/633286/feed.rss"))
# TODO Logic to monitor functionality of the scraper