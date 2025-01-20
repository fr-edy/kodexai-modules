import modules.bafin.scraper

if __name__ == "__main__":
    scraper = modules.bafin.scraper.BafinScraper()
    scraper.get_decrees()
