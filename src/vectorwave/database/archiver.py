import json
import os
from typing import Dict, Any, List
import weaviate.classes.query as wvc_query  # Using Weaviate v4 filters
from .db import get_cached_client           # Import within the same package
from ..models.db_config import get_weaviate_settings

class VectorWaveArchiver:
    def __init__(self):
        self.client = get_cached_client()
        self.settings = get_weaviate_settings()
        self.collection_name = self.settings.EXECUTION_COLLECTION_NAME

    def export_and_clear(self,
                         function_name: str,
                         output_file: str,
                         clear_after_export: bool = False,
                         delete_only: bool = False) -> Dict[str, int]:
        """
        Exports execution logs or cleans them up from the database.
        """
        collection = self.client.collections.get(self.collection_name)

        # 1. Configure the filter
        filters = wvc_query.Filter.by_property("function_name").equal(function_name)

        # Filter only successful logs if it's for training export
        if not delete_only:
            filters = filters & wvc_query.Filter.by_property("status").equal("SUCCESS")

        # 2. Retrieve data
        # UUID is automatically included in the fetch_objects result object (obj.uuid).
        response = collection.query.fetch_objects(
            filters=filters,
            limit=10000,
            return_properties=["return_value", "timestamp_utc"]
        )

        objects = response.objects
        if not objects:
            return {"exported": 0, "deleted": 0}

        exported_count = 0
        deleted_count = 0
        uuids_to_delete = []

        # 3. Save to file (Export mode)
        if not delete_only:
            try:
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)

                with open(output_file, 'a', encoding='utf-8') as f:
                    for obj in objects:
                        data_entry = self._convert_to_training_format(obj)
                        f.write(json.dumps(data_entry, ensure_ascii=False) + "\n")
                        uuids_to_delete.append(obj.uuid)
                        exported_count += 1
                print(f"✅ [Export] {exported_count} records saved: {output_file}")
            except Exception as e:
                print(f"❌ [Error] Failed to save file: {e}")
                return {"exported": 0, "deleted": 0} # Stop deletion upon save failure
        else:
            # If in delete-only mode, add all retrieved objects to the deletion list
            uuids_to_delete = [obj.uuid for obj in objects]

        # 4. Delete from DB (if option is enabled)
        if (clear_after_export or delete_only) and uuids_to_delete:
            try:
                # Use Weaviate v4 delete_many
                result = collection.data.delete_many(
                    where=wvc_query.Filter.by_id().contains_any(uuids_to_delete)
                )
                deleted_count = result.successful
                print(f"🗑️ [Clear] {deleted_count} records deleted from DB.")
            except Exception as e:
                print(f"❌ [Error] DB deletion failed: {e}")

        return {"exported": exported_count, "deleted": deleted_count}

    def _convert_to_training_format(self, obj) -> Dict[str, Any]:
        """
        Converts logs to LLM fine-tuning format (JSONL)
        """
        props = obj.properties
        exclude_keys = {
            'status', 'duration_ms', 'timestamp_utc', 'error_message', 'error_code',
            'return_value', 'function_name', 'trace_id', 'span_id', 'parent_span_id',
            'function_uuid', 'run_id', 'uuid'
        }

        inputs = {k: v for k, v in props.items() if k not in exclude_keys}
        output = props.get('return_value')

        return {
            "messages": [
                {"role": "user", "content": json.dumps(inputs, ensure_ascii=False)},
                {"role": "assistant", "content": str(output)}
            ]
        }