# 🧑🏻‍💻 Scraping Test Assignment 2

For the second assignment we would like to test how well we would work together in a scenario close to the real-world application. The task would be to write a scraper for European Central Bank (ECB) compatible with our backend. Attached you can find an archive with some code from our codebase you’ll need to finish the task.

## Task

You have to write a scraper for ECB’s website. This is a list of pages you’d need to scrape:
- `RegUpdateTypes.REGULATION`:
  - https://www.ecb.europa.eu/press/pubbydate/html/index.en.html?name_of_publication=Letters%20to%20MEPs
  - https://www.ecb.europa.eu/press/accounts/html/index.en.html
- `RegUpdateTypes.NEWS`:
  - https://www.ecb.europa.eu/press/pubbydate/html/index.en.html?name_of_publication=Press%20release
  - https://www.ecb.europa.eu/press/stats/paysec/html/index.en.html

From each link you should only process 10 latest publications. We’re only interested in the content in English. Like in the first assignment, you should scrape both the main publication link as well as any related articled/documents.

## Code

We use Poetry for dependency management. You’ll find a `pyproject.toml` in the archive with some packages you’ll need to install. One of them is the ScrapingBee SDK. You can create a free account with ScrapingBee and use it during development.
You’ll find an example of a scraper in `mas_scraper.py` . We would like you to implement `ecb_scraper.py` following the same structure & logic.
`main.py` imitates the cronjob handler that would start scraping jobs. You’ll find an example implementation for a different regulator included.
`models.py` and `utils.py` contain some additional code you’ll have to use to complete the assignment.
Follow TODOs left in the code to complete this assignment.