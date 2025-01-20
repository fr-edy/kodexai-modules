from dataclasses import dataclass


@dataclass
class DecreeResult:
    subtitle: str
    url_frag: str


def parse_decree(elem) -> DecreeResult:
    try:
        result = DecreeResult()
        result.subtitle = elem.find("p").text
        header_elem = elem.find("h3")
        result.url_frag = header_elem.find("a").get("href")

        # topline_elem = header_elem.find("span")
        # meta_elem = topline_elem.xpath("//div[contains(@class, 'metadata')]")
        # theme_elem = topline_elem.xpath("//div[contains(@class, 'thema')]")
        # theme = theme_elem.find("a").text()

    except Exception as e:
        print(e)
