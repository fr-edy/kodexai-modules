from lxml import etree
from typing import Optional, List


class HTMLParser:

    def __init__(self, data: str):
        if not data:
            raise ValueError("Empty HTML content.")

        self._data = data
        self._parse()

    def _parse(self) -> "HTMLParser":
        self._tree = etree.HTML(self._data)
        return self

    def find(self, tag: str, attrs: Optional[dict] = None) -> Optional[etree.Element]:
        if self._tree is None:
            raise ValueError("HTML content not parsed. Call parse() before find().")
        return self._tree.find(".//{}".format(tag), namespaces=attrs)

    def find_all(self, tag: str, attrs: Optional[dict] = None) -> List[etree.Element]:
        if self._tree is None:
            raise ValueError("HTML content not parsed. Call parse() before find_all().")
        return self._tree.findall(".//{}".format(tag), namespaces=attrs)

    def get_text(self) -> str:
        if self._tree is None:
            raise ValueError("HTML content not parsed. Call parse() before get_text().")
        return "".join(self._tree.itertext())

    def get(self) -> etree.ElementTree:
        if self._tree is None:
            raise ValueError("HTML content not parsed. Call parse() before get().")
        return self._tree
