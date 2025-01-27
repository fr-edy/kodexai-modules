URL = "https://www.ecb.europa.eu/foedb/dbs/foedb/publications.en/1737978659/8AvkKGF3/data/0/chunk_0.json"
from utils import load_page_content
from json import loads


txt = load_page_content(URL)
d = loads(txt)

idx = 0

while True:
    print("-----")
    print("ID:", d[idx])
    idx += 1
    print("Timestamp:", d[idx])
    idx += 1

    print("Year:", d[idx])
    idx += 1

    print("Unknown a:", d[idx])
    idx += 1
    print("Unknown b:", d[idx])
    idx += 1
    print("Unknown c:", d[idx])
    idx += 1

    print("Category:", d[idx])
    idx += 1
    print("Author:", d[idx])
    idx += 1
    print("Unknown 2:", d[idx])
    idx += 1
    print("Link:", d[idx])
    idx += 1
    print("Meta:", d[idx])
    idx += 1

    print("Related (a):", d[idx])
    idx += 1
    print("Related (b):", d[idx])
    idx += 1
    if idx >= len(d):
        break
