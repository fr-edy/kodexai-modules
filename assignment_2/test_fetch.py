import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from utils import load_page_content
from json import loads



class FoeDBFetcher:
    def __init__(self, host:str, database_name:str):
        self.config = {
            "host": host,
            "database_name": database_name,
            "database_version": None,
        }
        
        self.loaded_db = {}
        self.chunk_cache = {}

    def fetch_json(self, url: str) -> Dict:
        """Fetch JSON data from a URL."""
        txt = load_page_content(url)
        return loads(txt)

    def get_url(
        self,
        request: str,
        key: Optional[str] = None,
        value: Optional[Any] = None,
        item: Optional[Any] = None,
    ) -> str:
        """Generate URLs for different types of requests."""
        db_root = f"{self.config["host"]}/{self.config["database_name"]}/"

        if request == "versions":
            return f"{db_root}versions.json"

        versioned_root = f"{db_root}{self.loaded_db['database_version']}/{self.loaded_db['database_hash']}/"

        if request == "metadata":
            return f"{versioned_root}metadata.json"
        elif request == "index":
            if value is not None:
                index_value_id = self.loaded_db["indexes"][key][value]["index_value_id"]
                return (
                    f"{versioned_root}indexes/{key}/{index_value_id}/chunk_{item}.json"
                )
            return f"{versioned_root}indexes/{key}/index.json"
        elif request == "data":
            return f"{versioned_root}data/{key}/chunk_{value}.json"

        raise ValueError(f"Unknown request type: {request}")

    def get_chunk_id(self, sort_id: int) -> int:
        """Calculate chunk ID from sort ID."""
        return sort_id // self.loaded_db["metadata"]["chunk_size"]

    def get_chunk_group(self, chunk_id: int) -> int:
        """Calculate chunk group from chunk ID."""
        return chunk_id // self.loaded_db["metadata"]["chunk_group_size"]

    def get_chunk_offset(self, sort_id: int) -> int:
        """Calculate offset within chunk from sort ID."""
        return sort_id % self.loaded_db["metadata"]["chunk_size"]

    def build_data_from_chunk(self, sort_id: int, chunk: List) -> Dict:
        """Build item data from chunk data."""
        header = self.loaded_db["metadata"]["header"]
        start = self.get_chunk_offset(sort_id) * len(header)
        end = start + len(header)
        data = chunk[start:end]

        result = {}
        for i, field_name in enumerate(header):
            # Handle mapped values if they exist
            if (
                "loaded_maps" in self.loaded_db
                and field_name in self.loaded_db["loaded_maps"]
            ):
                result[field_name] = self.loaded_db["loaded_maps"][field_name]["index"][
                    data[i]
                ]
            else:
                result[field_name] = data[i]

        result["$foedb:id"] = sort_id
        return result

    def get_chunk(self, chunk_id: int) -> List:
        """Fetch chunk data if not in cache."""
        if chunk_id not in self.chunk_cache:
            chunk_group_id = self.get_chunk_group(chunk_id)
            self.chunk_cache[chunk_id] = self.fetch_json(
                self.get_url("data", str(chunk_group_id), chunk_id)
            )
        return self.chunk_cache[chunk_id]

    def get_data_by_id(self, sort_id: int) -> Dict:
        """Get item data by sort ID."""
        chunk = self.get_chunk(self.get_chunk_id(sort_id))
        return self.build_data_from_chunk(sort_id, chunk)

    def load_db(self):
        """Load database metadata and initialize structures."""
        # Fetch versions
        versions = self.fetch_json(self.get_url("versions"))

        # Set version and hash
        self.loaded_db["database_version"] = (
            self.config["database_version"] or versions[0]["version"]
        )
        self.loaded_db["database_hash"] = versions[0]["hash"]

        # Fetch metadata
        self.loaded_db["metadata"] = self.fetch_json(self.get_url("metadata"))

        # Initialize indexes
        self.loaded_db["indexes"] = {}
        for index in self.loaded_db["metadata"]["indexes"]:
            index_values = self.fetch_json(self.get_url("index", index))

            self.loaded_db["indexes"][index] = {}
            for idx, index_value in enumerate(index_values):
                self.loaded_db["indexes"][index][index_value["value"]] = {
                    "index_value_id": idx,
                    "total_records": index_value["total_records"],
                    "first_sort_id_per_chunk": index_value["first_sort_id_per_chunk"],
                    "last_sort_id_per_chunk": index_value["last_sort_id_per_chunk"],
                    "number_of_chunks": len(index_value["first_sort_id_per_chunk"]),
                    "sort_ids": [],
                }

    def fetch_all_items(self, batch_size: int = 100) -> List[Dict]:
        """Fetch all items from the database."""
        self.load_db()
        total_records = self.loaded_db["metadata"]["total_records"]

        all_items = []
        for start_idx in range(0, total_records, batch_size):
            batch_items = []
            end_idx = min(start_idx + batch_size, total_records)

            # Fetch each item in the batch
            for idx in range(start_idx, end_idx):
                batch_items.append(self.get_data_by_id(idx))

            all_items.extend(batch_items)

            print(f"Fetched items {start_idx} to {end_idx} of {total_records}")

        return all_items


def main():


    fetcher = FoeDBFetcher("https://www.ecb.europa.eu/foedb/dbs/foedb", "publications.en")

    try:
        items = fetcher.fetch_all_items(batch_size=100000)
        print(f"Successfully fetched {len(items)} items")

        # Example: Save to JSON file
        with open("database_items.json", "w") as f:
            json.dump(items, f, indent=2)

    except Exception as e:
        print(f"Error fetching items: {e}")


if __name__ == "__main__":
    main()
