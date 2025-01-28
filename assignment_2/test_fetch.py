import json
from typing import Dict, List, Optional, Any
from json import loads
import csv
import io
from utils import load_page_content

def parse_related_publication(raw_data: str) -> Dict:
    """
    Parse a single related publication string into a structured dictionary.
    """
    try:
        # Use CSV reader to properly handle quoted fields
        reader = csv.reader(io.StringIO(raw_data))
        fields = next(reader)  # Get the single row
        
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
            
        # Create structured output
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

def fetch_foe_db_data(host: str = "https://www.ecb.europa.eu/foedb/dbs/foedb", 
                     database_name: str = "publications.en", 
                     amount_to_fetch:int=10) -> List[Dict]:
    """
    Fetch all data from FoeDB with support for parsing related publications
    """
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
            return loads(txt)
            
        def get_url(request: str, key: Optional[str] = None, 
                   value: Optional[Any] = None, item: Optional[Any] = None) -> str:
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
            if chunk_id not in chunk_cache:
                chunk_group_id = chunk_id // loaded_db["metadata"]["chunk_group_size"]
                chunk_cache[chunk_id] = fetch_json(get_url("data", str(chunk_group_id), chunk_id))
            return chunk_cache[chunk_id]
            
        def get_data_by_id(sort_id: int) -> Dict:
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
                    # Special handling for relatedPublications field
                    if field_name in ["relatedPublications", "childrenPublication"] and isinstance(value, list):
                        parsed_publications = []
                        for pub in value:
                            if pub and isinstance(pub, str):
                                parsed_pub = parse_related_publication(pub)
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
        
        # Fetch all items
        total_records = loaded_db["metadata"]["total_records"]
        all_items = []
        
        # Fetch only amount_to_fetch items
        end_idx = min(amount_to_fetch, total_records)
        all_items = [get_data_by_id(idx) for idx in range(end_idx)]
        print(f"Fetched {end_idx} items out of {total_records} total records")
        
        return all_items
        
    except Exception as e:
        print(f"Error fetching items: {e}")
        return []

if __name__ == "__main__":
    items = fetch_foe_db_data()
    print(f"Successfully fetched {len(items)} items")
    
    # Save with nice formatting and ensure_ascii=False for proper character handling
    with open("database_items.json", "w", encoding='utf-8') as f:
        json.dump(items, f, indent=2, ensure_ascii=False)