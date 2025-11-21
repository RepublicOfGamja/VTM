import pytest
import json
import uuid
from unittest.mock import MagicMock, patch, mock_open
from vectorwave.database.archiver import VectorWaveArchiver
from vectorwave.models.db_config import WeaviateSettings
from weaviate.classes.query import Filter as wvc_filter # Import Filter explicitly

# --- Mock Fixtures ---

@pytest.fixture
def mock_archiver_deps(monkeypatch):
    """
    Mocks the dependencies (DB client, settings) for Archiver testing.
    """
    # 1. Mock Settings
    mock_settings = WeaviateSettings(EXECUTION_COLLECTION_NAME="TestExecutions")
    mock_get_settings = MagicMock(return_value=mock_settings)

    # 2. Mock Weaviate Client & Collection
    mock_client = MagicMock()
    mock_collection = MagicMock()

    # Set up the fake response object for query.fetch_objects() to return
    mock_query = MagicMock()
    mock_collection.query = mock_query

    # Set up the fake result object for data.delete_many() to return
    mock_data = MagicMock()
    mock_delete_result = MagicMock()
    mock_delete_result.successful = 5  # Assume 5 successful deletions
    mock_data.delete_many.return_value = mock_delete_result
    mock_collection.data = mock_data

    mock_client.collections.get.return_value = mock_collection
    mock_get_client = MagicMock(return_value=mock_client)

    # 3. Apply Monkeypatch
    monkeypatch.setattr("vectorwave.database.archiver.get_cached_client", mock_get_client)
    monkeypatch.setattr("vectorwave.database.archiver.get_weaviate_settings", mock_get_settings)

    return {
        "client": mock_client,
        "collection": mock_collection,
        "query": mock_query,
        "data": mock_data,
        "settings": mock_settings
    }

def create_mock_object(uuid_str, props):
    """Helper function to mimic a Weaviate Object"""
    mock_obj = MagicMock()
    mock_obj.uuid = uuid_str
    mock_obj.properties = props
    return mock_obj


# --- Test Cases ---

def test_export_and_clear_success(mock_archiver_deps):
    """
    Case 1: [Export + Clear] Normal operation test
    - Verify successful file saving
    - Verify DB deletion call
    """
    # Arrange
    valid_uuid_1 = str(uuid.uuid4())
    valid_uuid_2 = str(uuid.uuid4())

    mock_objects = [
        create_mock_object(valid_uuid_1, {"function_name": "test_func", "return_value": "res1", "status": "SUCCESS"}),
        create_mock_object(valid_uuid_2, {"function_name": "test_func", "return_value": "res2", "status": "SUCCESS"})
    ]
    mock_archiver_deps["query"].fetch_objects.return_value = MagicMock(objects=mock_objects)

    archiver = VectorWaveArchiver()

    # Act
    # Mocks os.makedirs and open to prevent actual file creation
    with patch("os.makedirs") as mock_makedirs, \
            patch("builtins.open", new_callable=mock_open) as mock_file:

        result = archiver.export_and_clear(
            function_name="test_func",
            output_file="data/dataset.jsonl",
            clear_after_export=True,  # <--- Request deletion after Export
            delete_only=False
        )

    # Assert
    # 1. Check result return value
    assert result["exported"] == 2
    assert result["deleted"] == 5  # Mocked value

    # 2. Verify file writing (called 2 times)
    assert mock_file.call_count == 1  # open() call count
    handle = mock_file()
    assert handle.write.call_count == 2 # write() call count (2 data records)

    # 3. Verify DB deletion call (delete_many was called)
    mock_archiver_deps["data"].delete_many.assert_called_once()

    # 4. Verify directory creation
    mock_makedirs.assert_called_with("data", exist_ok=True)


def test_export_only_no_delete(mock_archiver_deps):
    """
    Case 2: [Export Only] Only exports and does not delete
    """
    # Arrange
    valid_uuid = str(uuid.uuid4())
    mock_objects = [create_mock_object(valid_uuid, {"val": 1})]
    mock_archiver_deps["query"].fetch_objects.return_value = MagicMock(objects=mock_objects)

    archiver = VectorWaveArchiver()

    # Act
    with patch("os.makedirs"), patch("builtins.open", new_callable=mock_open):
        result = archiver.export_and_clear(
            function_name="test_func",
            output_file="backup.jsonl",
            clear_after_export=False, # <--- No deletion
            delete_only=False
        )

    # Assert
    assert result["exported"] == 1
    assert result["deleted"] == 0

    # DB deletion method should not be called
    mock_archiver_deps["data"].delete_many.assert_not_called()


def test_delete_only_no_export(mock_archiver_deps):
    """
    Case 3: [Delete Only] Performs only deletion without saving file (Purge)
    """
    # Arrange
    valid_uuid = str(uuid.uuid4())
    mock_objects = [create_mock_object(valid_uuid, {"val": 2})]
    mock_archiver_deps["query"].fetch_objects.return_value = MagicMock(objects=mock_objects)

    archiver = VectorWaveArchiver()

    # Act
    with patch("builtins.open", new_callable=mock_open) as mock_file:
        result = archiver.export_and_clear(
            function_name="test_func",
            output_file="",
            clear_after_export=False,
            delete_only=True  # <--- Delete-only mode
        )

    # Assert
    assert result["exported"] == 0
    assert result["deleted"] == 5

    # File should not be opened
    mock_file.assert_not_called()
    # DB deletion should be called
    mock_archiver_deps["data"].delete_many.assert_called_once()


def test_safety_check_file_write_error_prevents_delete(mock_archiver_deps):
    """
    Case 4: [Safety] If an error occurs during file saving, DB deletion must be prevented
    """
    # Arrange
    valid_uuid = str(uuid.uuid4())
    mock_objects = [create_mock_object(valid_uuid, {"data": "ok"})]
    mock_archiver_deps["query"].fetch_objects.return_value = MagicMock(objects=mock_objects)

    archiver = VectorWaveArchiver()

    # Act
    # Induce IOError when open() is called
    with patch("os.makedirs"), \
            patch("builtins.open", side_effect=IOError("Disk Full")):

        result = archiver.export_and_clear(
            function_name="test_func",
            output_file="crash.jsonl",
            clear_after_export=True,  # <--- Deletion requested, but
            delete_only=False
        )

    # Assert
    # 1. Check result
    assert result["exported"] == 0
    assert result["deleted"] == 0

    # 2. CRITICAL: DB deletion must never be called
    mock_archiver_deps["data"].delete_many.assert_not_called()


def test_convert_to_training_format_logic(mock_archiver_deps):
    """
    Case 5: Test data format conversion logic (JSONL format)
    """
    archiver = VectorWaveArchiver()

    # Mock Object Properties
    valid_uuid = str(uuid.uuid4())
    props = {
        "function_name": "calc",
        "status": "SUCCESS",
        "input_a": 10,       # Input value
        "input_b": 20,       # Input value
        "return_value": 30,  # Output value
        "duration_ms": 100,  # Value to be excluded
        "uuid": valid_uuid   # Value to be excluded (assuming inclusion in properties)
    }
    mock_obj = create_mock_object(valid_uuid, props)

    # Act
    formatted = archiver._convert_to_training_format(mock_obj)

    # Assert
    assert "messages" in formatted
    messages = formatted["messages"]
    assert len(messages) == 2

    # Verify User Message (Input) - checking excluded keys are missing
    user_content = json.loads(messages[0]["content"])
    assert user_content == {"input_a": 10, "input_b": 20}
    assert "status" not in user_content
    assert "duration_ms" not in user_content
    assert "uuid" not in user_content

    # Verify Assistant Message (Output)
    assert messages[1]["content"] == "30"