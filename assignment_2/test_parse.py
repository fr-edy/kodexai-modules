URL = "https://www.ecb.europa.eu/foedb/dbs/foedb/publications.en/1737978659/8AvkKGF3/data/0/chunk_0.json"
from utils import load_page_content
from json import loads
from dataclasses import dataclass

txt = load_page_content(URL)
d = loads(txt)


def parse_publication_types(timestamp: int, hash: str) -> dict[int, str]:
    publications_raw: dict[int, str] = loads(
        load_page_content(
            f"https://www.ecb.europa.eu/foedb/dbs/foedb/publications_types/{timestamp}/{hash}/data/0/chunk_0.json"
        )
    )
    publications_mapping = {}
    i = 0
    while i < len(publications_raw):
        publications_mapping[publications_raw[i]] = publications_raw[i + 1]
        i += 2
    return publications_mapping


idx = 0

publications_mapping = parse_publication_types("1733394927", "YOIkkD7N")


@dataclass
class Post:
    id: str
    timestamp: int
    year: int

    authors: list[str]
    title: str
    related: list[any]
    url: str
    category: str
    jel_code: str
    publication_type: str  # 226:


def parse_annex_or_related(arr: list[any]) -> Post:
    try:
        id = arr[0]
        timestamp = arr[1]
        year = arr[2]
        unknown_1 = arr[3]
        publication_id = arr[4]

        url = ""
        link_raw = arr[9]
        link_arr = link_raw.replace('""', '"')[1:-1]
        if not link_arr.endswith('"]'):
            link_arr += '"]'

        if link_arr:
            url = loads(link_arr)[0]

        title = ""

        meta_raw: str = arr[11]
        meta_raw_clean = meta_raw.replace('""', '"')[1:-1]
        if (
            meta_raw_clean and not "Summary" in meta_raw_clean
        ):  # edge case - summary instead of title
            meta = loads(meta_raw_clean)
            title = meta.get("Title", "")
        elif "Summary" in meta_raw_clean:
            meta = loads('{"' + meta_raw_clean)
            title = meta.get("Summary", "")

        return Post(
            id=id,
            timestamp=timestamp,
            year=year,
            authors="",
            title=title,
            related="",
            url=url,
            category="",
            jel_code="",
            publication_type=publications_mapping.get(publication_id, ""),
        )
    except Exception as e:
        print("ERROR:", e, arr)
        return None


def parse_entry(data: list[any], idx: int) -> tuple[Post, int]:
    id = data[idx]
    idx += 1
    timestamp = data[idx]
    idx += 1

    year = data[idx]
    idx += 1

    # print("Unknown a:", data[idx])
    idx += 1
    publication_id = data[idx]
    idx += 1
    jel_code = data[idx]
    idx += 1

    category = data[idx]
    idx += 1
    authors1 = data[idx] or ""
    idx += 1
    authors2 = data[idx] or ""
    authors = []
    if authors1:
        [authors.append(x) for x in authors1.split("|") if x]
    if authors2:
        [authors.append(x) for x in authors2.split("|") if x]
    idx += 1
    url = data[idx]
    idx += 1
    meta = data[idx]
    title = meta["Title"]
    idx += 1

    annexes_raw = data[idx]
    idx += 1
    related_raw = data[idx]
    idx += 1

    for r in related_raw:
        entry = r.split(",")
        print(" - related", parse_annex_or_related(entry))

    for r in annexes_raw:
        entry = r.split(",")
        print(" - annex", parse_annex_or_related(entry))

    if not publications_mapping.get(publication_id, False):
        print("No publication type", publication_id)

    return (
        Post(
            id=id,
            timestamp=timestamp,
            year=year,
            authors=authors,
            category=category,
            url=url,
            title=title,
            related=[],  # TODO
            jel_code=jel_code,
            publication_type=publications_mapping.get(publication_id, ""),
        ),
        idx,
    )


while True:
    post, idx = parse_entry(d, idx)
    print("\n--\n", post)
    if idx >= len(d):
        break
