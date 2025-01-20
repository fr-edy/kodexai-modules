from lxml import etree
from typing import Optional, List


class HTMLParser:

    def __init__(self, data: str):
        if not data:
            raise ValueError("Empty HTML content.")

        self._data = data
        self._parse()

    def _parse(self) -> "HTMLParser":
        self.tree = etree.HTML(self._data)
        return self

    def xpath(self, query):
        return self.tree.xpath(query)

    def find(self, tag: str, attrs: Optional[dict] = None) -> Optional[etree.Element]:
        return self.tree.find(".//{}".format(tag), namespaces=attrs)

    def find_all(self, tag: str, attrs: Optional[dict] = None) -> List[etree.Element]:
        return self.tree.findall("{}".format(tag), namespaces=attrs)

    def get_text(self) -> str:
        return "".join(self.tree.itertext())
