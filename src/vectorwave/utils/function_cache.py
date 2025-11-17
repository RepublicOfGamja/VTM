import hashlib
import json
import logging
import os
from typing import Dict, Any

logger = logging.getLogger(__name__)

CACHE_FILE_NAME = ".vectorwave_functions_cache.json"


class FunctionCacheManager:
    """Manages the local file cache for VectorWave function definitions (static data)."""

    def __init__(self, cache_dir: str = "."):
        # Set cache file path (defaults to the current execution directory)
        self.cache_path = os.path.join(cache_dir, CACHE_FILE_NAME)
        self.cache: Dict[str, str] = self._load_cache()
        logger.info(f"FunctionCacheManager initialized. Cache file: {self.cache_path}")

    def _load_cache(self) -> Dict[str, str]:
        """Loads the cache from the JSON file."""
        if not os.path.exists(self.cache_path):
            return {}
        try:
            with open(self.cache_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            # If file loading or JSON parsing fails, start in a clean state.
            logger.warning(f"Failed to load static function cache from {self.cache_path}. Starting clean. Error: {e}")
            return {}

    def _save_cache(self):
        """Saves the cache to the JSON file."""
        try:
            with open(self.cache_path, 'w', encoding='utf-8') as f:
                # Use `sort_keys=True` to ensure file content consistency.
                json.dump(self.cache, f, indent=4, sort_keys=True)
        except IOError as e:
            logger.error(f"Failed to save static function cache to {self.cache_path}. Error: {e}")

    @staticmethod
    def calculate_content_hash(func_identifier: str, static_properties: Dict[str, Any]) -> str:
        """
        Calculates a unique SHA256 hash based on the function's content and static metadata.
        """
        content_data = {
            "identifier": func_identifier,
            # The static_properties dictionary is included.
            "static_props": static_properties
        }

        # Create a JSON string, sorting keys to ensure hash stability.
        content_str = json.dumps(content_data, sort_keys=True, ensure_ascii=True)

        return hashlib.sha256(content_str.encode('utf-8')).hexdigest()

    def is_cached_and_unchanged(self, func_uuid: str, current_hash: str) -> bool:
        """
        Checks if the function (by UUID) is in the cache and its hash value matches.
        """
        return self.cache.get(func_uuid) == current_hash

    def update_cache(self, func_uuid: str, current_hash: str):
        """
        Updates the cache with the new hash and saves it to the file.
        """
        self.cache[func_uuid] = current_hash
        self._save_cache()


# Creates a singleton instance of FunctionCacheManager at the module level.
function_cache_manager = FunctionCacheManager()
