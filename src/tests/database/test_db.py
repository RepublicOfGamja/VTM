import pytest
from unittest.mock import MagicMock, patch, ANY
import weaviate
import weaviate.classes.config as wvc
# Import the specific driver exception to mock it
from weaviate.exceptions import WeaviateConnectionError as WeaviateClientConnectionError

# Import functions to be tested
# (Assuming pytest is run from the project root and pytest.ini is set)
from vectorwave.database.db import get_weaviate_client, create_vectorwave_schema
from vectorwave.models.db_config import WeaviateSettings, get_weaviate_settings
from vectorwave.exception.exceptions import (
    WeaviateConnectionError,
    WeaviateNotReadyError,
    SchemaCreationError
)

# --- Test Fixtures ---

@pytest.fixture
def test_settings() -> WeaviateSettings:
    """Returns a test Weaviate settings object."""
    return WeaviateSettings(
        WEAVIATE_HOST="test.host.local",
        WEAVIATE_PORT=1234,
        WEAVIATE_GRPC_PORT=5678,
        COLLECTION_NAME="TestCollection",
        IS_VECTORIZE_COLLECTION_NAME=False
    )

# --- Tests for get_weaviate_client ---

@patch('vectorwave.database.db.weaviate.connect_to_local')
def test_get_weaviate_client_success(mock_connect_to_local, test_settings):
    """
    Case 1: Weaviate connection is successful.
    - .connect_to_local() should be called.
    - .is_ready() should return True.
    - The created client object should be returned.
    """
    # 1. Arrange
    mock_client = MagicMock(spec=weaviate.WeaviateClient)
    mock_client.is_ready.return_value = True
    mock_connect_to_local.return_value = mock_client

    # 2. Act
    client = get_weaviate_client(settings=test_settings)

    # 3. Assert
    # Check if 'connect_to_local' was called once with the correct args
    mock_connect_to_local.assert_called_once_with(
        host=test_settings.WEAVIATE_HOST,
        port=test_settings.WEAVIATE_PORT,
        grpc_port=test_settings.WEAVIATE_GRPC_PORT
    )
    mock_client.is_ready.assert_called_once()
    assert client == mock_client


@patch('vectorwave.database.db.weaviate.connect_to_local')
def test_get_weaviate_client_connection_refused(mock_connect_to_local, test_settings):
    """
    Case 2: Connection is refused because Weaviate server is down.
    - Should raise WeaviateConnectionError.
    """
    # 1. Arrange
    # Mock the original Weaviate driver exception
    mock_connect_to_local.side_effect = WeaviateClientConnectionError("Connection refused")

    # 2. Act & 3. Assert
    with pytest.raises(WeaviateConnectionError) as exc_info:
        get_weaviate_client(settings=test_settings)

    # Check if the error message from the original exception is included
    assert "Connection refused" in str(exc_info.value)
    assert "Failed to connect to Weaviate" in str(exc_info.value)


@patch('vectorwave.database.db.weaviate.connect_to_local')
def test_get_weaviate_client_not_ready(mock_connect_to_local, test_settings):
    """
    Case 3: Connected, but Weaviate is not ready (.is_ready() returns False).
    - Should raise WeaviateNotReadyError.
    """
    # 1. Arrange
    mock_client = MagicMock(spec=weaviate.WeaviateClient)
    mock_client.is_ready.return_value = False # This is the trigger
    mock_connect_to_local.return_value = mock_client

    # 2. Act & 3. Assert
    with pytest.raises(WeaviateNotReadyError) as exc_info:
        get_weaviate_client(settings=test_settings)

    assert "server is not ready" in str(exc_info.value)


# --- Tests for create_vectorwave_schema ---

def test_create_schema_new(test_settings):
    """
    Case 4: Schema doesn't exist and is created successfully.
    - .collections.exists() returns False.
    - .collections.create() should be called.
    - .collections.get() should not be called.
    """
    # 1. Arrange
    mock_client = MagicMock(spec=weaviate.WeaviateClient)
    mock_collections = MagicMock()
    mock_collections.exists.return_value = False # Trigger for creation
    mock_new_collection = MagicMock()
    mock_collections.create.return_value = mock_new_collection
    mock_client.collections = mock_collections

    # 2. Act
    collection = create_vectorwave_schema(mock_client, test_settings)

    # 3. Assert
    mock_collections.exists.assert_called_once_with(test_settings.COLLECTION_NAME)
    mock_collections.create.assert_called_once()

    # Check if 'create' was called with the correct 'name'
    call_args = mock_collections.create.call_args
    assert call_args.kwargs.get('name') == test_settings.COLLECTION_NAME

    # Check if key properties were passed
    passed_props = [prop.name for prop in call_args.kwargs.get('properties', [])]
    assert "function_name" in passed_props
    assert "source_code" in passed_props

    mock_collections.get.assert_not_called()
    assert collection == mock_new_collection


def test_create_schema_existing(test_settings):
    """
    Case 5: Schema already exists.
    - .collections.exists() returns True.
    - .collections.create() should not be called.
    - .collections.get() should be called.
    """
    # 1. Arrange
    mock_client = MagicMock(spec=weaviate.WeaviateClient)
    mock_collections = MagicMock()
    mock_collections.exists.return_value = True # Trigger for skipping
    mock_existing_collection = MagicMock()
    mock_collections.get.return_value = mock_existing_collection
    mock_client.collections = mock_collections

    # 2. Act
    collection = create_vectorwave_schema(mock_client, test_settings)

    # 3. Assert
    mock_collections.exists.assert_called_once_with(test_settings.COLLECTION_NAME)
    mock_collections.create.assert_not_called()
    mock_collections.get.assert_called_once_with(test_settings.COLLECTION_NAME)
    assert collection == mock_existing_collection


def test_create_schema_creation_error(test_settings):
    """
    Case 6: An error occurs during schema creation (e.g., bad API key).
    - Should raise SchemaCreationError.
    """
    # 1. Arrange
    mock_client = MagicMock(spec=weaviate.WeaviateClient)
    mock_collections = MagicMock()
    mock_collections.exists.return_value = False
    # Set .create() to raise an exception
    mock_collections.create.side_effect = Exception("Invalid OpenAI API Key")
    mock_client.collections = mock_collections

    # 2. Act & 3. Assert
    with pytest.raises(SchemaCreationError) as exc_info:
        create_vectorwave_schema(mock_client, test_settings)

    assert "Error during schema creation" in str(exc_info.value)
    assert "Invalid OpenAI API Key" in str(exc_info.value)