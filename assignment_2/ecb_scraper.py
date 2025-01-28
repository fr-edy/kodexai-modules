import logging
import unicodedata
from datetime import datetime
from urllib.parse import urljoin
import json
import csv
import io
from typing import List, Dict, Any, Optional
from lxml.etree import HTML
from utils import load_page_content
from models import Regulators, RegUpdateTypes

log = logging.getLogger(__name__)

# Constants to replace enums
REGULATOR_ECB = {
    "name": Regulators.ECB,
    "base_url": Regulators.ECB.base_url
}

# Publication types constants
UPDATE_TYPE_REGULATION = "REGULATION"
UPDATE_TYPE_PRESS_RELEASE = "PRESS_RELEASE"

# News publication types constants
NEWS_TYPE_PRESS_RELEASE = 1  # Press releases / Press 
NEWS_TYPE_LETTER_TO_MEPS = 18  # Letter to MEPs

def _create_publication(
    web_title: str,
    published_at: datetime,
    web_url: str,
    update_type: RegUpdateTypes,
    category: str = "",
    related_urls: List[str] = None
) -> Dict:
    """Creates a publication dictionary with the given parameters."""
    return {
        "regulator": REGULATOR_ECB,
        "type": update_type,
        "web_title": web_title,
        "published_at": published_at,
        "web_url": web_url,
        "category": category,
        "related_urls": related_urls or []
    }

def load_publications(
    publications_url: str,
    updates_type: str
) -> List[Dict]:
    """Loads the last 10 publications from the ECB website and extracts the PDF links."""
    return _load_last_publications(publications_url, updates_type)

def load_publications_lazy_loaded(
    publications_url: str,
    updates_type: str
) -> List[Dict]:
    """Loads the last 10 publications from the ECB website and extracts the PDF links."""
    return _load_last_publications(publications_url, updates_type)

def _load_last_publications(
    url: str,
    updates_type: str
) -> List[Dict]:
    """Loads and parses the most recent publications from the ECB website."""
    html = HTML(load_page_content(url))
    parsed_publications = []

    # Get matching dt/dd pairs that contain publication info
    for dt, dd in zip(html.xpath(".//dt"), html.xpath(".//dd")):
        # Extract core publication data
        date_text = dt.xpath(".//text()")[0].strip()
        title_element = dd.xpath(".//a")
        title_text = title_element[0].text.strip()
        web_url = urljoin(REGULATOR_ECB["base_url"], title_element[0].get("href"))

        # Get any PDF links from the description
        related_urls = [
            urljoin(REGULATOR_ECB["base_url"], href.strip())
            for href in dd.xpath(".//dl//a/@href")
        ]

        # Create publication dictionary with normalized text
        publication = _create_publication(
            web_title=unicodedata.normalize("NFKC", title_text),
            published_at=datetime.strptime(date_text, "%d %B %Y"),
            web_url=web_url,
            update_type=updates_type,
            related_urls=related_urls
        )
        parsed_publications.append(publication)

    log.info(
        f"Found {len(parsed_publications)} publication links on the ECB page {url}"
    )
    return parsed_publications

def load_publications_from_db(update_type: RegUpdateTypes, amount_to_fetch: int = 10) -> List[Dict]:
    """Loads the last publications from the ECB database."""
    pub_type = NEWS_TYPE_LETTER_TO_MEPS if update_type == UPDATE_TYPE_REGULATION else NEWS_TYPE_PRESS_RELEASE
    return _load_publications_db(update_type, pub_type, amount_to_fetch)

def _load_publications_db(update_type: RegUpdateTypes, pub_type: int, amount_to_fetch: int = 10) -> List[Dict]:
    """Internal function to load publications from database."""
    releases = _fetch_foe_db_data(amount_to_fetch=5000)  # Returns descending by date
    matching_releases = []
    
    for release in releases:
        if release["type"] == pub_type:
            matching_releases.append(release)
            if len(matching_releases) >= amount_to_fetch:
                break
                
    return [_parse_db_publications_as_publication(update_type, r) for r in matching_releases]

def _parse_db_publications_as_publication(update_type: RegUpdateTypes, release: Dict) -> Dict:
    """Converts a database release to a publication dictionary."""
    return _create_publication(
        web_title=release["publicationProperties"]["Title"],
        published_at=datetime.fromtimestamp(release["pub_timestamp"]),
        web_url=urljoin(REGULATOR_ECB["base_url"], release["documentTypes"][0]),
        update_type=update_type,
        category="" if release["Taxonomy"] is None else release["Taxonomy"],
        related_urls=[
            urljoin(REGULATOR_ECB["base_url"], pdf_url)
            for pub in release["childrenPublication"]
            for pdf_url in pub["pdfUrls"]
        ]
    )

def _fetch_foe_db_data(
    host: str = "https://www.ecb.europa.eu/foedb/dbs/foedb",
    database_name: str = "publications.en",
    amount_to_fetch: int = 10
) -> List[Dict]:
    """Fetches data from FoeDB with support for parsing related publications."""
    try:
        # Initialize basic configurations
        config = {
            "host": host,
            "database_name": database_name,
            "database_version": None
        }
        
        loaded_db = {}
        chunk_cache = {}
        
        def fetch_json(url: str) -> Dict:
            txt = load_page_content(url)
            return json.loads(txt)
            
        def get_url(request: str, key: Optional[str] = None, 
                   value: Optional[Any] = None, item: Optional[Any] = None) -> str:
            """Constructs URLs for different FoeDB API endpoints based on the request type.
            
            Args:
            request: Type of request (versions, metadata, index, data)
            key: Optional key for index/data requests
            value: Optional value for index requests or chunk number for data
            item: Optional chunk number for index requests
            
            Returns:
            str: Constructed URL for the requested endpoint
            """

            db_root = f"{config['host']}/{config['database_name']}/"
            
            if request == "versions":
                return f"{db_root}versions.json"
                
            versioned_root = f"{db_root}{loaded_db['database_version']}/{loaded_db['database_hash']}/"
            
            if request == "metadata":
                return f"{versioned_root}metadata.json"
            elif request == "index":
                if value is not None:
                    index_value_id = loaded_db["indexes"][key][value]["index_value_id"]
                    return f"{versioned_root}indexes/{key}/{index_value_id}/chunk_{item}.json"
                return f"{versioned_root}indexes/{key}/index.json"
            elif request == "data":
                return f"{versioned_root}data/{key}/chunk_{value}.json"
            
            raise ValueError(f"Unknown request type: {request}")
            
        def get_chunk(chunk_id: int) -> List:
            """
            Retrieves a chunk of data from cache or fetches it from the server if not cached.

            Args:
                chunk_id (int): The ID of the chunk to retrieve.

            Returns:
                List: The requested data chunk.

            Description:
                This function implements a caching mechanism for data chunks. If the requested chunk
                is not in cache, it calculates the chunk group ID and fetches the data from server,
                storing it in cache before returning. If the chunk is already cached, it returns
                the cached version directly.
            """
            if chunk_id not in chunk_cache:
                chunk_group_id = chunk_id // loaded_db["metadata"]["chunk_group_size"]
                chunk_cache[chunk_id] = fetch_json(get_url("data", str(chunk_group_id), chunk_id))
            return chunk_cache[chunk_id]
            
        def get_data_by_id(sort_id: int) -> Dict:
            """
            Retrieves data from database by sort ID and constructs a dictionary with mapped values.
            The function gets a chunk of data based on the sort ID, maps the values according to loaded maps,
            and handles special cases for publication-related fields.
            Args:
                sort_id (int): The sorting ID used to locate the data in the database.
            Returns:
                Dict: A dictionary containing:
                    - Mapped values from the database using header field names as keys
                    - Original values for unmapped fields
                    - Parsed publication data for 'relatedPublications' and 'childrenPublication' fields
                    - Original sort_id as '$foedb:id'
            """
            chunk_id = sort_id // loaded_db["metadata"]["chunk_size"]
            chunk = get_chunk(chunk_id)
            
            header = loaded_db["metadata"]["header"]
            start = (sort_id % loaded_db["metadata"]["chunk_size"]) * len(header)
            end = start + len(header)
            data = chunk[start:end]
            
            result = {}
            for i, field_name in enumerate(header):
                if "loaded_maps" in loaded_db and field_name in loaded_db["loaded_maps"]:
                    result[field_name] = loaded_db["loaded_maps"][field_name]["index"][data[i]]
                else:
                    value = data[i]
                    if field_name in ["relatedPublications", "childrenPublication"] and isinstance(value, list):
                        parsed_publications = []
                        for pub in value:
                            if pub and isinstance(pub, str):
                                parsed_pub = _parse_related_publication(pub)
                                if parsed_pub:
                                    parsed_publications.append(parsed_pub)
                        value = parsed_publications
                    result[field_name] = value
                    
            result["$foedb:id"] = sort_id
            return result
        
        # Load database metadata
        versions = fetch_json(get_url("versions"))
        loaded_db["database_version"] = config["database_version"] or versions[0]["version"]
        loaded_db["database_hash"] = versions[0]["hash"]
        loaded_db["metadata"] = fetch_json(get_url("metadata"))
        loaded_db["indexes"] = {}
        
        # Initialize indexes
        for index in loaded_db["metadata"]["indexes"]:
            index_values = fetch_json(get_url("index", index))
            loaded_db["indexes"][index] = {}
            for idx, index_value in enumerate(index_values):
                loaded_db["indexes"][index][index_value["value"]] = {
                    "index_value_id": idx,
                    "total_records": index_value["total_records"],
                    "first_sort_id_per_chunk": index_value["first_sort_id_per_chunk"],
                    "last_sort_id_per_chunk": index_value["last_sort_id_per_chunk"],
                    "number_of_chunks": len(index_value["first_sort_id_per_chunk"]),
                    "sort_ids": [],
                }
        
        # Fetch items
        total_records = loaded_db["metadata"]["total_records"]
        end_idx = min(amount_to_fetch, total_records)
        all_items = [get_data_by_id(idx) for idx in range(end_idx)]
        print(f"Fetched {end_idx} items out of {total_records} total records")
        
        return all_items
        
    except Exception as e:
        print(f"Error fetching items: {e}")
        return []

def _parse_related_publication(raw_data: str) -> Dict:
    """Parses a single related publication string into a structured dictionary."""
    try:
        reader = csv.reader(io.StringIO(raw_data))
        fields = next(reader)
        
        # Extract the known fields
        pub_id = fields[0]
        timestamp = fields[1]
        year = fields[2]
        month = fields[3]
        day = fields[4]
        
        # Parse the PDF URLs list (field 9)
        try:
            pdf_urls = json.loads(fields[9].replace('\\"', '"'))
        except (json.JSONDecodeError, IndexError):
            pdf_urls = []
            
        # Parse the metadata JSON (field 10)
        try:
            metadata = json.loads(fields[10].replace('\\"', '"'))
        except (json.JSONDecodeError, IndexError):
            metadata = {}
            
        return {
            "publicationId": pub_id,
            "timestamp": timestamp,
            "date": {
                "year": year,
                "month": month,
                "day": day
            },
            "pdfUrls": pdf_urls,
            "metadata": metadata
        }
    except Exception as e:
        print(f"Error parsing related publication: {e}")
        return {}